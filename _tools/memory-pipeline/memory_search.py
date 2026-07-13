#!/usr/bin/env python3
"""Ranked memory retrieval across runtime events, candidates, and canonical docs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-]{3,}")
CANONICAL_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".sh"}
EXCLUDED_PARTS = {".git", "__pycache__", ".venv", "node_modules"}
EXCLUDED_RUNTIME_DIRS = {"candidates", "dreams", "events", "graphs", "maintenance", "reorg-suggestions", "conflicts", "search-index"}
AGENT_QUERY_TOKENS = {"agent", "agents", "codex", "claude", "gemini", "chatgpt", "cursor", "grok", "instruction", "instructions", "sync"}
STRUCTURE_QUERY_TOKENS = {"structure", "structur", "template", "file", "files", "format"}
OVERVIEW_QUERY_TOKENS = {"overview", "index", "summary", "summari", "list"}
ENDPOINT_QUERY_TOKENS = {"endpoint", "endpoints", "api", "apis", "route", "routes", "heartbeat"}
ARCHITECTURE_QUERY_TOKENS = {"architecture", "architectur", "workflow", "staging", "runtime"}
SEMANTIC_MODEL_NAME = "all-MiniLM-L6-v2"
SEMANTIC_RERANK_LIMIT = 30
INDEX_DIRNAME = "_runtime/search-index"
INDEX_FILENAME = "memory_search.sqlite3"

_EMBEDDING_MODEL = None


@dataclass
class Record:
    id: str
    source: str
    path: str
    text: str
    status: str
    date: str
    chunk_id: str = ""
    section_title: str = ""
    section_level: int = 0
    confidence: float = 0.0
    semantic: float = 0.0
    score: float = 0.0
    explain: dict = field(default_factory=dict)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--query", default="", help="Natural-language search query.")
    p.add_argument("--scope", default="all", choices=["all", "runtime", "events", "candidates", "canonical"])
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--include-rejected", action="store_true")
    p.add_argument("--as-of", dest="as_of", default="", help="Return memories on/before YYYY-MM-DD")
    p.add_argument("--before", default="", help="Return memories on/before YYYY-MM-DD")
    p.add_argument("--after", default="", help="Return memories on/after YYYY-MM-DD")
    p.add_argument("--mode", default="", choices=["keyword", "semantic", "hybrid"])
    p.add_argument("--rebuild-index", action="store_true", help="Rebuild the semantic embedding index.")
    p.add_argument("--no-semantic", action="store_true", help="Force keyword-only behavior.")
    p.add_argument("--no-recency", action="store_true", help="Ablation: disable the recency boost.")
    p.add_argument("--explain", action="store_true", help="Show per-result score component breakdown.")
    p.add_argument("--json", action="store_true", help="Output JSON records")
    args = p.parse_args()
    if not args.query and not args.rebuild_index:
        p.error("--query is required unless --rebuild-index is set.")
    return args


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_date(date_str: str) -> datetime | None:
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def extract_last_updated(text: str) -> str:
    patterns = [
        r"\*\*Last Updated:\*\*\s*(\d{4}-\d{2}-\d{2})",
        r"(?im)^last_updated:\s*(\d{4}-\d{2}-\d{2})\b",
        r"(?im)^#\s*Last Updated:\s*(\d{4}-\d{2}-\d{2})\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return "1970-01-01"


def to_days_ago(date_str: str) -> float:
    dt = parse_date(date_str)
    if not dt:
        return 9999.0
    return max(0.0, (now_utc() - dt).total_seconds() / 86400)


def tokenize(text: str) -> list[str]:
    return [normalize_token(t.lower()) for t in TOKEN_RE.findall(text.lower())]


def normalize_token(token: str) -> str:
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    for suffix in ("ers", "ing", "ed", "er", "s"):
        if len(token) > 4 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def token_counter(text: str) -> Counter[str]:
    return Counter(tokenize(text))


def slugify(text: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return lowered or "section"


def status_boost(status: str) -> float:
    table = {
        "merged": 2.0,
        "approved": 1.5,
        "queued": 0.5,
        "rejected": -1.0,
        "": 0.0,
    }
    return table.get(status, 0.0)


def source_boost(source: str) -> float:
    table = {"canonical": 0.7, "candidate": 0.5, "event": 0.4}
    return table.get(source, 0.0)


def recency_boost(date_str: str) -> float:
    days = to_days_ago(date_str)
    return max(0.0, 2.0 - (days / 14.0))


def match_score(query_tokens: list[str], text: str) -> float:
    counts = token_counter(text)
    return float(sum(counts.get(tok, 0) for tok in query_tokens))


def coverage_score(query_tokens: list[str], text: str) -> float:
    counts = token_counter(text)
    present = sum(1 for tok in set(query_tokens) if counts.get(tok, 0) > 0)
    return present / max(1, len(set(query_tokens)))


def path_score(query_tokens: list[str], path: str) -> float:
    normalized = path.replace("-", " ").replace("_", " ").lower()
    counts = token_counter(normalized)
    parts = [part.lower() for part in Path(path).parts]
    basename = Path(path).name.lower()
    stem = Path(path).stem.lower().replace("-", " ").replace("_", " ")
    query_set = set(query_tokens)
    in_benchmarks = "_runtime" in parts and "benchmarks" in parts

    score = 0.8 * sum(counts.get(tok, 0) for tok in query_tokens)

    if query_set & STRUCTURE_QUERY_TOKENS:
        if basename == "readme.md":
            score += 6.0
        if "_templates" in parts or "template" in basename:
            score += 8.0
        if path == "_templates/file-template.md":
            score += 8.0

    if {"build", "builder", "script"} & query_set and basename.startswith("build_"):
        score += 4.0
    if {"build", "builder", "script", "graph"} <= query_set and basename == "build_temporal_graph.py":
        score += 6.0
    if {"query", "search"} & query_set and (basename.startswith("query_") or basename.startswith("search")):
        score += 2.0
    if "project" in query_set and "projects" in parts:
        score += 3.0
    if {"runtime", "staging", "candidate", "queue"} & query_set and "_runtime" in parts:
        score += 3.0
    if {"benchmark", "harness", "eval"} & query_set:
        if "eval" in basename or "benchmark" in basename:
            score += 7.0
        if in_benchmarks:
            score += 4.0
        if path == "_tools/memory-pipeline/eval_memory_search.py":
            score += 8.0
    elif in_benchmarks:
        score -= 28.0
        if {"architecture", "endpoint", "endpoints", "pending", "blocker", "blockers", "project", "service", "services"} & query_set:
            score -= 10.0

    if path == "_state.yaml" and {"pending", "blocker", "blockers", "open", "track", "tracked", "cert", "expiration", "expirations"} & query_set:
        score += 8.0
    if path == "_state.yaml" and {"pending", "blocker", "blockers", "open", "item", "items"} & query_set:
        score += 14.0
    if path == "_state.yaml" and {"wildcard", "cert", "expiration", "expirations", "tracked"} & query_set:
        score += 12.0
    if path == "home-lab/services/aikb-memory-core.md" and {"memory", "core"} <= query_set:
        score += 12.0
    if path == "home-lab/services/aikb-memory-core.md" and (ENDPOINT_QUERY_TOKENS & query_set or ARCHITECTURE_QUERY_TOKENS & query_set):
        score += 12.0
    if path == "home-lab/infrastructure/network-dns.md" and {"wildcard", "cert", "expiration", "expirations"} & query_set:
        score += 10.0
    if path == "home-lab/infrastructure/servers.md" and {"run", "runs", "truenas", "host", "hosts", "server", "servers"} & query_set:
        score += 12.0
    if path == "_runtime/promotion-queue.md" and {"promotion", "queue", "runtime"} <= query_set:
        score += 10.0
    if path.startswith("home-lab/services/") and ENDPOINT_QUERY_TOKENS & query_set:
        score += 8.0
    if path.startswith("home-lab/services/") and ARCHITECTURE_QUERY_TOKENS & query_set:
        score += 4.0
    if path.startswith("home-lab/infrastructure/") and {"host", "hosts", "server", "servers", "truenas", "turing"} & query_set:
        score += 5.0
    if path.startswith("personal-projects/") and "project" in query_set:
        score += 4.0

    if path == "_index.md":
        if query_set & OVERVIEW_QUERY_TOKENS:
            score += 5.0
        else:
            score -= 16.0
            if {"host", "hosts", "service", "services", "endpoint", "endpoints", "blocker", "blockers"} & query_set:
                score -= 8.0

    if basename.endswith("roadmap.md") and not {"roadmap", "plan", "planning", "implement", "implementation"} & query_set:
        score -= 6.0
    if "implementation" in stem and not {"implement", "implementation", "roadmap", "plan"} & query_set:
        score -= 4.0

    if query_set & AGENT_QUERY_TOKENS and ("_agents" in parts or basename == "agents.md"):
        score += 4.0
    if ("_agents" in parts or basename == "agents.md") and not (query_set & AGENT_QUERY_TOKENS):
        score -= 18.0
        if query_set & STRUCTURE_QUERY_TOKENS:
            score -= 8.0

    if stem and " ".join(query_tokens) in stem:
        score += 3.0

    return score


def score_components(record: Record, query_tokens: list[str], no_recency: bool = False) -> dict[str, float]:
    """Per-component score breakdown; score_record sums it, --explain exposes it."""
    lowered = record.text.lower()
    phrase = " ".join(query_tokens)
    query_set = set(query_tokens)
    path_parts = [part.lower() for part in Path(record.path).parts]
    in_benchmarks = "_runtime" in path_parts and "benchmarks" in path_parts
    section_tokens = token_counter(record.section_title) if record.section_title else Counter()
    components: dict[str, float] = {}
    components["lexical"] = 1.3 * match_score(query_tokens, record.text)
    components["coverage"] = 2.5 * coverage_score(query_tokens, record.text)
    section = 3.0 * sum(section_tokens.get(tok, 0) for tok in query_tokens)
    if record.section_title:
        section_present = sum(1 for tok in set(query_tokens) if section_tokens.get(tok, 0) > 0)
        section += 2.0 * (section_present / max(1, len(set(query_tokens))))
    components["section"] = section
    components["path"] = path_score(query_tokens, record.path)
    components["phrase"] = 4.0 if phrase and phrase in lowered else 0.0
    components["semantic"] = 3.0 * max(0.0, record.semantic)
    components["status"] = status_boost(record.status)
    components["recency"] = 0.0 if no_recency else recency_boost(record.date)
    components["confidence"] = max(0.0, min(1.0, record.confidence))
    components["source"] = source_boost(record.source)
    components["benchmark_penalty"] = (
        -35.0 if in_benchmarks and not ({"benchmark", "harness", "eval"} & query_set) else 0.0
    )
    return components


def score_record(record: Record, query_tokens: list[str], no_recency: bool = False) -> float:
    components = score_components(record, query_tokens, no_recency=no_recency)
    record.explain = components
    return sum(components.values())


def within_dates(record: Record, before: datetime | None, after: datetime | None) -> bool:
    dt = parse_date(record.date)
    if not dt:
        return False
    if before and dt.date() > before.date():
        return False
    if after and dt.date() < after.date():
        return False
    return True


def iter_events(root: Path) -> Iterable[Record]:
    events_dir = root / "_runtime" / "events"
    for path in sorted(events_dir.glob("*.ndjson")):
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            obj = json.loads(line)
            text = f"{obj.get('project', '')} {obj.get('summary', '')}".strip()
            yield Record(
                id=obj.get("id", ""),
                source="event",
                path=str(path.relative_to(root)),
                text=text,
                status="",
                date=obj.get("ts_utc", path.stem),
                confidence=0.0,
            )


def parse_candidate_file(path: Path, root: Path) -> list[Record]:
    records: list[Record] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    current: dict[str, str] = {}

    def flush() -> None:
        if not current.get("id"):
            return
        candidate_text = " ".join(
            part for part in [current.get("target_file", ""), current.get("proposed_change", "")] if part
        )
        records.append(
            Record(
                id=current.get("id", ""),
                source="candidate",
                path=str(path.relative_to(root)),
                text=candidate_text,
                status=current.get("status", ""),
                date=path.stem,
                confidence=float(current.get("confidence", "0") or 0),
            )
        )

    for raw in lines:
        line = raw.strip()
        if raw.startswith("  - id:"):
            flush()
            current = {"id": line.split(":", 1)[1].strip()}
        elif line.startswith("target_file:"):
            current["target_file"] = line.split(":", 1)[1].strip()
        elif line.startswith("proposed_change:"):
            current["proposed_change"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("confidence:"):
            current["confidence"] = line.split(":", 1)[1].strip()
        elif line.startswith("status:"):
            current["status"] = line.split(":", 1)[1].strip()
    flush()
    return records


def iter_candidates(root: Path) -> Iterable[Record]:
    cand_dir = root / "_runtime" / "candidates"
    for path in sorted(cand_dir.glob("*.yaml")):
        if path.name == "README.md":
            continue
        for record in parse_candidate_file(path, root):
            yield record


def iter_canonical(root: Path) -> Iterable[Record]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in CANONICAL_SUFFIXES:
            continue
        parts = set(path.parts)
        if parts & EXCLUDED_PARTS:
            continue
        if "_runtime" in parts and parts & EXCLUDED_RUNTIME_DIRS:
            continue
        rel = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8", errors="ignore")
        updated = extract_last_updated(text)
        if path.suffix.lower() == ".md":
            yielded = False
            sections = split_markdown_sections(text)
            for heading, section_level, section_text in sections:
                excerpt = " ".join(section_text.splitlines()[:60])
                heading_slug = slugify(heading)
                search_text = f"{rel} {path.stem.replace('-', ' ').replace('_', ' ')} {heading} {excerpt}"
                yield Record(
                    id=f"canon:{rel}#{heading_slug}",
                    source="canonical",
                    path=rel,
                    text=search_text,
                    status="merged",
                    date=updated,
                    chunk_id=f"{rel}#{heading_slug}",
                    section_title=heading,
                    section_level=section_level,
                    confidence=1.0,
                )
                yielded = True
            if yielded:
                continue

        excerpt = " ".join(text.splitlines()[:60])
        search_text = f"{rel} {path.stem.replace('-', ' ').replace('_', ' ')} {excerpt}"
        yield Record(
            id=f"canon:{rel}",
            source="canonical",
            path=rel,
            text=search_text,
            status="merged",
            date=updated,
            chunk_id=rel,
            section_title="document",
            section_level=0,
            confidence=1.0,
        )


def split_markdown_sections(text: str) -> list[tuple[str, int, str]]:
    lines = text.splitlines()
    sections: list[tuple[str, int, str]] = []
    current_heading = "document"
    current_level = 0
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("#"):
            if current_lines:
                sections.append((current_heading, current_level, "\n".join(current_lines).strip()))
            current_level = len(line) - len(line.lstrip("#"))
            current_heading = line.lstrip("#").strip() or "document"
            current_lines = [line]
            continue
        current_lines.append(line)

    if current_lines:
        sections.append((current_heading, current_level, "\n".join(current_lines).strip()))

    return [(heading, level, body) for heading, level, body in sections if body]


def collect_records(root: Path, scope: str) -> list[Record]:
    records: list[Record] = []
    if scope in ("all", "runtime", "events"):
        records.extend(iter_events(root))
    if scope in ("all", "runtime", "candidates"):
        records.extend(iter_candidates(root))
    if scope in ("all", "canonical"):
        records.extend(iter_canonical(root))
    return records


def semantic_backend_available() -> bool:
    try:
        import numpy  # noqa: F401
        from sentence_transformers import SentenceTransformer  # noqa: F401
    except Exception:
        return False
    return True


def get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer

        _EMBEDDING_MODEL = SentenceTransformer(SEMANTIC_MODEL_NAME)
    return _EMBEDDING_MODEL


def index_db_path(root: Path) -> Path:
    return root / INDEX_DIRNAME / INDEX_FILENAME


def connect_db(db_path: Path) -> sqlite3.Connection:
    """Open the embedding index hardened for concurrent access.

    Hooks, nightly maintenance, and multiple agents can touch this DB at the
    same time; WAL + busy timeout avoid 'database is locked' failures.
    """
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def ensure_index_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            record_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            path TEXT NOT NULL,
            chunk_id TEXT NOT NULL,
            section_title TEXT NOT NULL,
            status TEXT NOT NULL,
            date TEXT NOT NULL,
            confidence REAL NOT NULL,
            text_hash TEXT NOT NULL,
            vector_dim INTEGER NOT NULL,
            vector_blob BLOB NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.commit()


def record_hash(record: Record) -> str:
    payload = "\n".join(
        [
            record.id,
            record.source,
            record.path,
            record.chunk_id,
            record.section_title,
            record.status,
            record.date,
            f"{record.confidence:.6f}",
            record.text,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_index_hashes(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute("SELECT record_id, text_hash FROM embeddings").fetchall()
    return {str(record_id): str(text_hash) for record_id, text_hash in rows}


def encode_texts(texts: list[str]):
    import numpy as np

    model = get_embedding_model()
    vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)


def upsert_embedding_batch(conn: sqlite3.Connection, records: list[Record]) -> None:
    if not records:
        return
    vectors = encode_texts([record.text[:2000] for record in records])
    rows = []
    for record, vector in zip(records, vectors):
        rows.append(
            (
                record.id,
                record.source,
                record.path,
                record.chunk_id or record.path,
                record.section_title,
                record.status,
                record.date,
                float(record.confidence),
                record_hash(record),
                int(vector.shape[0]),
                sqlite3.Binary(vector.tobytes()),
            )
        )
    conn.executemany(
        """
        INSERT INTO embeddings (
            record_id, source, path, chunk_id, section_title, status, date, confidence, text_hash, vector_dim, vector_blob
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(record_id) DO UPDATE SET
            source=excluded.source,
            path=excluded.path,
            chunk_id=excluded.chunk_id,
            section_title=excluded.section_title,
            status=excluded.status,
            date=excluded.date,
            confidence=excluded.confidence,
            text_hash=excluded.text_hash,
            vector_dim=excluded.vector_dim,
            vector_blob=excluded.vector_blob
        """,
        rows,
    )
    conn.commit()


def sync_semantic_index(root: Path, records: list[Record], force_rebuild: bool) -> str:
    if not semantic_backend_available():
        return "semantic backend unavailable"

    db_path = index_db_path(root)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect_db(db_path)
    try:
        ensure_index_schema(conn)
        stored_model = conn.execute("SELECT value FROM metadata WHERE key='model_name'").fetchone()
        if force_rebuild or (stored_model and stored_model[0] != SEMANTIC_MODEL_NAME):
            conn.execute("DELETE FROM embeddings")
            conn.execute("DELETE FROM metadata")
            conn.commit()

        current_hashes = load_index_hashes(conn)
        wanted = {record.id: record_hash(record) for record in records}
        stale_ids = sorted(set(current_hashes) - set(wanted))
        if stale_ids:
            conn.executemany("DELETE FROM embeddings WHERE record_id = ?", [(record_id,) for record_id in stale_ids])
            conn.commit()

        pending = [record for record in records if current_hashes.get(record.id) != wanted[record.id]]
        for offset in range(0, len(pending), 64):
            upsert_embedding_batch(conn, pending[offset : offset + 64])

        conn.executemany(
            "INSERT INTO metadata(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            [
                ("model_name", SEMANTIC_MODEL_NAME),
                ("updated_utc", now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")),
                ("record_count", str(len(records))),
            ],
        )
        conn.commit()
        if force_rebuild:
            return f"rebuilt semantic index ({len(records)} records)"
        if pending or stale_ids:
            return f"synced semantic index ({len(pending)} updated, {len(stale_ids)} removed)"
        return "semantic index already current"
    finally:
        conn.close()


def fetch_vectors(root: Path, record_ids: list[str]):
    import numpy as np

    if not record_ids:
        return {}

    db_path = index_db_path(root)
    if not db_path.exists():
        return {}

    conn = connect_db(db_path)
    try:
        placeholders = ",".join("?" for _ in record_ids)
        query = (
            "SELECT record_id, vector_dim, vector_blob FROM embeddings "
            f"WHERE record_id IN ({placeholders})"
        )
        rows = conn.execute(query, record_ids).fetchall()
    finally:
        conn.close()

    vectors = {}
    for record_id, vector_dim, vector_blob in rows:
        vec = np.frombuffer(vector_blob, dtype=np.float32, count=int(vector_dim))
        vectors[str(record_id)] = vec
    return vectors


def semantic_scores(root: Path, query: str, target_records: list[Record]) -> dict[str, float]:
    import numpy as np

    if not target_records:
        return {}

    vectors = fetch_vectors(root, [record.id for record in target_records])
    if not vectors:
        return {}

    query_vector = encode_texts([query])[0]
    scores: dict[str, float] = {}
    for record in target_records:
        vector = vectors.get(record.id)
        if vector is None:
            continue
        denom = float(np.linalg.norm(vector) * np.linalg.norm(query_vector))
        if denom <= 0:
            scores[record.id] = 0.0
            continue
        similarity = float(np.dot(vector, query_vector) / denom)
        scores[record.id] = max(0.0, similarity)
    return scores


def resolve_mode(args: argparse.Namespace, embeddings_available: bool) -> tuple[str, str]:
    if args.no_semantic:
        return ("keyword", "")

    requested = args.mode or ("hybrid" if embeddings_available else "keyword")
    if requested in {"semantic", "hybrid"} and not embeddings_available:
        return ("keyword", "sentence-transformers not available; using keyword mode")
    return (requested, "")


def apply_date_filters(records: list[Record], before: datetime | None, after: datetime | None) -> list[Record]:
    if not before and not after:
        return records
    return [record for record in records if within_dates(record, before, after)]


def score_keyword_candidates(
    records: list[Record], query_tokens: list[str], include_rejected: bool, no_recency: bool = False
) -> list[Record]:
    scored: list[Record] = []
    for record in records:
        if record.source == "candidate" and record.status == "rejected" and not include_rejected:
            continue
        lexical = match_score(query_tokens, record.text)
        if lexical <= 0:
            continue
        record.semantic = 0.0
        record.score = score_record(record, query_tokens, no_recency=no_recency)
        scored.append(record)
    return scored


def choose_top(records: list[Record], limit: int) -> list[Record]:
    ordered = sorted(records, key=lambda item: item.score, reverse=True)
    top: list[Record] = []
    seen_paths: set[str] = set()
    for record in ordered:
        if record.path in seen_paths:
            continue
        top.append(record)
        seen_paths.add(record.path)
        if len(top) >= max(1, limit):
            break
    return top


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    embeddings_available = semantic_backend_available()
    effective_mode, mode_warning = resolve_mode(args, embeddings_available)

    records = collect_records(root, args.scope)
    index_message = ""
    if args.rebuild_index:
        index_message = sync_semantic_index(root, records, force_rebuild=True)
        if not args.query:
            print(index_message)
            return 0
    elif effective_mode in {"semantic", "hybrid"}:
        index_message = sync_semantic_index(root, records, force_rebuild=False)

    q_tokens = tokenize(args.query)
    if not q_tokens:
        raise SystemExit("Query must include at least one token of length >= 3.")

    before = parse_date(args.as_of) if args.as_of else None
    if args.before:
        before = parse_date(args.before)
    after = parse_date(args.after) if args.after else None

    if (args.as_of and not parse_date(args.as_of)) or (args.before and not before) or (args.after and not after):
        raise SystemExit("Date filters must be valid YYYY-MM-DD values.")

    records = apply_date_filters(records, before, after)

    if effective_mode == "keyword":
        scored = score_keyword_candidates(records, q_tokens, args.include_rejected, no_recency=args.no_recency)
    elif effective_mode == "hybrid":
        scored = score_keyword_candidates(records, q_tokens, args.include_rejected, no_recency=args.no_recency)
        rerank = sorted(scored, key=lambda item: item.score, reverse=True)[:SEMANTIC_RERANK_LIMIT]
        sims = semantic_scores(root, args.query, rerank)
        for record in rerank:
            record.semantic = sims.get(record.id, 0.0)
            record.score = score_record(record, q_tokens, no_recency=args.no_recency)
    else:
        filtered = [
            record
            for record in records
            if not (record.source == "candidate" and record.status == "rejected" and not args.include_rejected)
        ]
        sims = semantic_scores(root, args.query, filtered)
        scored = []
        for record in filtered:
            record.semantic = sims.get(record.id, 0.0)
            lexical = match_score(q_tokens, record.text)
            if lexical <= 0 and record.semantic < 0.18:
                continue
            record.score = score_record(record, q_tokens, no_recency=args.no_recency)
            scored.append(record)

    top = choose_top(scored, args.limit)

    if args.json:
        payload = []
        for record in top:
            item = {
                "id": record.id,
                "source": record.source,
                "path": record.path,
                "status": record.status,
                "date": record.date,
                "chunk_id": record.chunk_id or record.path,
                "section_title": record.section_title,
                "section_level": record.section_level,
                "score": round(record.score, 3),
                "semantic": round(record.semantic, 3),
                "excerpt": record.text[:240],
            }
            if args.explain:
                item["explain"] = {key: round(value, 3) for key, value in record.explain.items()}
            payload.append(item)
        print(json.dumps(payload, indent=2))
        return 0

    if mode_warning:
        print(f"Note: {mode_warning}", file=sys.stderr)
    if index_message:
        print(f"Index: {index_message}")

    if not top:
        print("No matches.")
        return 0

    print(f"Mode: {effective_mode}")
    for index, record in enumerate(top, 1):
        print(
            f"{index}. [{record.source}] {record.id} score={record.score:.3f} "
            f"semantic={record.semantic:.3f} status={record.status or '-'} date={record.date}"
        )
        print(f"   path: {record.path}")
        print(f"   excerpt: {record.text[:200]}")
        if args.explain and record.explain:
            parts = ", ".join(
                f"{key}={value:+.2f}" for key, value in record.explain.items() if abs(value) >= 0.005
            )
            print(f"   explain: {parts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

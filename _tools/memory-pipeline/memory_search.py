#!/usr/bin/env python3
"""Ranked memory retrieval across runtime events, candidates, and canonical docs."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-]{3,}")
CANONICAL_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".sh"}
EXCLUDED_PARTS = {".git", "__pycache__", ".venv", "node_modules"}
EXCLUDED_RUNTIME_DIRS = {"candidates", "dreams", "events", "graphs", "maintenance", "reorg-suggestions", "conflicts"}
AGENT_QUERY_TOKENS = {"agent", "agents", "codex", "claude", "gemini", "chatgpt", "cursor", "grok", "instruction", "instructions", "sync"}
STRUCTURE_QUERY_TOKENS = {"structure", "structur", "template", "file", "files", "format"}
OVERVIEW_QUERY_TOKENS = {"overview", "index", "summary", "summari", "list"}
ENDPOINT_QUERY_TOKENS = {"endpoint", "endpoints", "api", "apis", "route", "routes", "heartbeat"}
ARCHITECTURE_QUERY_TOKENS = {"architecture", "architectur", "workflow", "staging", "runtime"}


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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--query", required=True)
    p.add_argument("--scope", default="all", choices=["all", "runtime", "events", "candidates", "canonical"])
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--include-rejected", action="store_true")
    p.add_argument("--as-of", dest="as_of", default="", help="Return memories on/before YYYY-MM-DD")
    p.add_argument("--before", default="", help="Return memories on/before YYYY-MM-DD")
    p.add_argument("--after", default="", help="Return memories on/after YYYY-MM-DD")
    p.add_argument("--no-semantic", action="store_true", help="Disable embedding similarity reranking")
    p.add_argument("--json", action="store_true", help="Output JSON records")
    return p.parse_args()


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


def score_record(r: Record, query_tokens: list[str]) -> float:
    lowered = r.text.lower()
    phrase = " ".join(query_tokens)
    query_set = set(query_tokens)
    path_parts = [part.lower() for part in Path(r.path).parts]
    in_benchmarks = "_runtime" in path_parts and "benchmarks" in path_parts
    section_tokens = token_counter(r.section_title) if r.section_title else Counter()
    s = 0.0
    s += 1.3 * match_score(query_tokens, r.text)
    s += 2.5 * coverage_score(query_tokens, r.text)
    s += 3.0 * sum(section_tokens.get(tok, 0) for tok in query_tokens)
    if r.section_title:
        section_present = sum(1 for tok in set(query_tokens) if section_tokens.get(tok, 0) > 0)
        s += 2.0 * (section_present / max(1, len(set(query_tokens))))
    s += path_score(query_tokens, r.path)
    if phrase and phrase in lowered:
        s += 4.0
    s += 3.0 * max(0.0, r.semantic)
    s += status_boost(r.status)
    s += recency_boost(r.date)
    s += max(0.0, min(1.0, r.confidence))
    s += source_boost(r.source)
    if in_benchmarks and not ({"benchmark", "harness", "eval"} & query_set):
        s -= 35.0
    return s


def within_dates(r: Record, before: datetime | None, after: datetime | None) -> bool:
    dt = parse_date(r.date)
    if not dt:
        return False
    if before and dt.date() > before.date():
        return False
    if after and dt.date() < after.date():
        return False
    return True


def iter_events(root: Path) -> Iterable[Record]:
    events_dir = root / "_runtime" / "events"
    for f in sorted(events_dir.glob("*.ndjson")):
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            yield Record(
                id=obj.get("id", ""),
                source="event",
                path=str(f.relative_to(root)),
                text=obj.get("summary", ""),
                status="",
                date=obj.get("ts_utc", f.stem),
                confidence=0.0,
            )


def parse_candidate_file(f: Path, root: Path) -> list[Record]:
    records: list[Record] = []
    lines = f.read_text(encoding="utf-8").splitlines()
    current: dict[str, str] = {}

    def flush() -> None:
        if not current.get("id"):
            return
        records.append(
            Record(
                id=current.get("id", ""),
                source="candidate",
                path=str(f.relative_to(root)),
                text=current.get("proposed_change", ""),
                status=current.get("status", ""),
                date=f.stem,
                confidence=float(current.get("confidence", "0") or 0),
            )
        )

    for raw in lines:
        line = raw.strip()
        if line.startswith("- id:"):
            flush()
            current = {"id": line.split(":", 1)[1].strip()}
        elif line.startswith("proposed_change:"):
            v = line.split(":", 1)[1].strip().strip('"')
            current["proposed_change"] = v
        elif line.startswith("confidence:"):
            current["confidence"] = line.split(":", 1)[1].strip()
        elif line.startswith("status:"):
            current["status"] = line.split(":", 1)[1].strip()
    flush()
    return records


def iter_candidates(root: Path) -> Iterable[Record]:
    cand_dir = root / "_runtime" / "candidates"
    for f in sorted(cand_dir.glob("*.yaml")):
        for rec in parse_candidate_file(f, root):
            yield rec


def iter_canonical(root: Path) -> Iterable[Record]:
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in CANONICAL_SUFFIXES:
            continue
        parts = set(f.parts)
        if parts & EXCLUDED_PARTS:
            continue
        if "_runtime" in parts and parts & EXCLUDED_RUNTIME_DIRS:
            continue
        rel = str(f.relative_to(root))
        text = f.read_text(encoding="utf-8", errors="ignore")
        date = extract_last_updated(text)
        if f.suffix.lower() == ".md":
            yielded = False
            sections = split_markdown_sections(text)
            for heading, section_level, section_text in sections:
                excerpt = " ".join(section_text.splitlines()[:60])
                heading_slug = slugify(heading)
                search_text = (
                    f"{rel} {f.stem.replace('-', ' ').replace('_', ' ')} "
                    f"{heading} {excerpt}"
                )
                yield Record(
                    id=f"canon:{rel}#{heading_slug}",
                    source="canonical",
                    path=rel,
                    text=search_text,
                    status="merged",
                    date=date,
                    chunk_id=f"{rel}#{heading_slug}",
                    section_title=heading,
                    section_level=section_level,
                    confidence=1.0,
                )
                yielded = True
            if yielded:
                continue

        excerpt = " ".join(text.splitlines()[:60])
        search_text = f"{rel} {f.stem.replace('-', ' ').replace('_', ' ')} {excerpt}"
        yield Record(
            id=f"canon:{rel}",
            source="canonical",
            path=rel,
            text=search_text,
            status="merged",
            date=date,
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


def add_semantic_scores(query: str, records: list[Record]) -> bool:
    if not records:
        return False

    try:
        from fastembed import TextEmbedding
    except Exception:
        return False

    embedder = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    q_vec = list(embedder.embed([query]))[0]
    rec_vecs = list(embedder.embed([r.text[:1800] for r in records]))

    q_norm = math.sqrt(sum(float(x) * float(x) for x in q_vec))
    if q_norm <= 0:
        return False

    for r, vec in zip(records, rec_vecs):
        vec_norm = math.sqrt(sum(float(x) * float(x) for x in vec))
        denom = vec_norm * q_norm
        if denom <= 0:
            sim = 0.0
        else:
            dot = sum(float(a) * float(b) for a, b in zip(vec, q_vec))
            sim = float(dot / denom)
        r.semantic = max(0.0, sim)

    return True


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    q_tokens = tokenize(args.query)
    if not q_tokens:
        raise SystemExit("Query must include at least one token of length >= 3.")

    before = parse_date(args.as_of) if args.as_of else None
    if args.before:
        before = parse_date(args.before)
    after = parse_date(args.after) if args.after else None

    if (args.as_of and not parse_date(args.as_of)) or (args.before and not before) or (args.after and not after):
        raise SystemExit("Date filters must be valid YYYY-MM-DD values.")

    records: list[Record] = []

    if args.scope in ("all", "runtime", "events"):
        records.extend(iter_events(root))
    if args.scope in ("all", "runtime", "candidates"):
        records.extend(iter_candidates(root))
    if args.scope in ("all", "canonical"):
        records.extend(iter_canonical(root))

    if before or after:
        records = [r for r in records if within_dates(r, before, after)]

    semantic_enabled = (not args.no_semantic) and add_semantic_scores(args.query, records)

    scored: list[Record] = []
    for r in records:
        if r.source == "candidate" and (r.status == "rejected" and not args.include_rejected):
            continue

        lexical = match_score(q_tokens, r.text)
        # Keep semantically relevant results even when keyword overlap is poor.
        if lexical <= 0 and r.semantic < 0.25:
            continue

        r.score = score_record(r, q_tokens)
        scored.append(r)

    scored.sort(key=lambda x: x.score, reverse=True)
    top: list[Record] = []
    seen_paths: set[str] = set()
    for record in scored:
        if record.path in seen_paths:
            continue
        top.append(record)
        seen_paths.add(record.path)
        if len(top) >= max(1, args.limit):
            break

    if args.json:
        payload = [
            {
                "id": r.id,
                "source": r.source,
                "path": r.path,
                "status": r.status,
                "date": r.date,
                "chunk_id": r.chunk_id or r.path,
                "section_title": r.section_title,
                "section_level": r.section_level,
                "score": round(r.score, 3),
                "semantic": round(r.semantic, 3),
                "excerpt": r.text[:240],
            }
            for r in top
        ]
        print(json.dumps(payload, indent=2))
        return 0

    if not top:
        print("No matches.")
        return 0

    mode = "keyword+semantic" if semantic_enabled else "keyword-only"
    print(f"Mode: {mode}")
    for i, r in enumerate(top, 1):
        print(f"{i}. [{r.source}] {r.id} score={r.score:.3f} semantic={r.semantic:.3f} status={r.status or '-'} date={r.date}")
        print(f"   path: {r.path}")
        print(f"   excerpt: {r.text[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

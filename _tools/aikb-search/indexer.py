#!/usr/bin/env python3
"""
AIKB Semantic Indexer

Walks AIKB markdown files, splits by H2 section, embeds with
fastembed (all-MiniLM-L6-v2 / ONNX, fully local), and stores in SQLite:
  - chunks table       — metadata + embedding BLOBs (numpy float32)
  - chunks_fts table   — FTS5 virtual table for BM25 keyword search

Run directly to rebuild the index:
    python3 indexer.py [--force]

The git post-commit hook calls this automatically when .md files change.
"""

import json
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import yaml

# ── Paths ──────────────────────────────────────────────────────────────────────
TOOL_DIR  = Path(__file__).parent
AIKB_ROOT = TOOL_DIR.parent.parent          # _tools/aikb-search/ → AIKB/
DB_PATH   = TOOL_DIR / "aikb_index.db"

# Directories to skip when walking AIKB
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules"}

# Filename patterns to skip: search-eval reports echo the eval queries and
# gold paths verbatim, so indexing them contaminates retrieval (the report
# outranks the documents it grades).
SKIP_FILE_RE = re.compile(r"search-eval")

# ── Embedding (lazy singleton) ─────────────────────────────────────────────────
_embedder = None


def _fastembed_cache_dir() -> Path:
    """Resolve fastembed cache directory used by huggingface_hub downloads."""
    return Path("/tmp/fastembed_cache")


def _reset_fastembed_model_cache() -> None:
    """
    Remove known all-MiniLM cache dirs to recover from partial/corrupt downloads.
    Safe to call even if paths do not exist.
    """
    cache = _fastembed_cache_dir()
    targets = [
        cache / "models--qdrant--all-MiniLM-L6-v2-onnx",
    ]
    for target in targets:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)


def get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        # Downloads ~23 MB on first use, cached under /tmp/fastembed_cache
        _embedder = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    return _embedder


def _is_missing_onnx_model_error(exc: Exception) -> bool:
    text = str(exc)
    return "NO_SUCHFILE" in text and "model.onnx" in text


def embed(texts: list[str]) -> list[np.ndarray]:
    """Return list of float32 unit vectors, one per text."""
    global _embedder
    try:
        embedder = get_embedder()
        return list(embedder.embed(texts))
    except Exception as exc:
        # Self-heal from partial/corrupt model cache by forcing a clean download.
        if not _is_missing_onnx_model_error(exc):
            raise
        print("⚠️  fastembed cache appears incomplete (missing model.onnx). Repairing cache and retrying once...")
        _reset_fastembed_model_cache()
        _embedder = None
        embedder = get_embedder()
        return list(embedder.embed(texts))

# ── Parsing ────────────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter block. Returns (metadata, body)."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            try:
                fm = yaml.safe_load(text[3:end]) or {}
            except yaml.YAMLError:
                fm = {}
            return fm, text[end + 4:].lstrip()
    return {}, text


def normalize_entity_name(value) -> str | None:
    # Underscores normalize to hyphens so runtime_cli.py and "runtime cli"
    # land on the same entity segments.
    name = str(value).strip().lower().replace("_", "-")
    if len(name) < 3 or name.isdigit():
        return None
    return name


def frontmatter_values(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, dict):
        return [str(item) for item in value.keys()]
    return [str(item) for item in re.split(r"[\s,]+", str(value)) if item]


def file_entities(file_path: Path, fm: dict) -> list[tuple[str, str]]:
    entities: list[tuple[str, str]] = []

    for tag in frontmatter_values(fm.get("tags")):
        name = normalize_entity_name(tag)
        if name:
            entities.append((name, "tag"))

    for host in frontmatter_values(fm.get("hosts")):
        name = normalize_entity_name(host)
        if name:
            entities.append((name, "host"))

    name = normalize_entity_name(file_path.stem)
    if name:
        entities.append((name, "file"))

    seen = set()
    unique_entities = []
    for name, kind in entities:
        key = (name, kind)
        if key in seen:
            continue
        seen.add(key)
        unique_entities.append((name, kind))
    return unique_entities


# ── Content entity extraction (deterministic) ──────────────────────────────────
# Regex/heuristic only — no LLM/ML dependency. An optional local-LLM enrichment
# pass (llm_enrich.py) can add richer entities where an endpoint is available.

ALIAS_PATH = TOOL_DIR / "entity_aliases.yaml"

# Host-domain suffixes come from the `_host_domains` config key in
# entity_aliases.yaml (underscore keys are config, not alias groups), so the
# shared code carries no personal domains.
_host_re_cache: re.Pattern | None = None


def _host_re() -> re.Pattern:
    global _host_re_cache
    if _host_re_cache is None:
        domains = []
        if ALIAS_PATH.exists():
            try:
                raw = yaml.safe_load(ALIAS_PATH.read_text(encoding="utf-8")) or {}
                domains = [str(d).strip().lstrip(".") for d in raw.get("_host_domains", []) if d]
            except yaml.YAMLError:
                pass
        if domains:
            alt = "|".join(re.escape(d) for d in domains)
            _host_re_cache = re.compile(rf"\b([a-z0-9][a-z0-9-]{{1,40}})\.(?:{alt})\b", re.I)
        else:
            _host_re_cache = re.compile(r"(?!x)x")  # matches nothing
    return _host_re_cache
_IP_RE = re.compile(r"\b((?:\d{1,3}\.){3}\d{1,3})\b")
_PATH_RE = re.compile(
    r"\b((?:_tools|_runtime|_agents|_templates|docs|home-lab|side-gigs|projects|personal[\w-]*)"
    r"(?:/[\w.-]+)*/[\w.-]+\.(?:py|sh|md|ya?ml|json))\b"
)
_BACKTICK_RE = re.compile(r"`([A-Za-z0-9_./:-]{3,40})`")
_CAMEL_RE = re.compile(r"\b([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\b")
_PORT_RE = re.compile(r"\bport\s+(\d{2,5})\b", re.I)
_WORD_RE = re.compile(r"[a-z0-9_-]{3,40}")

# Generic terms that CamelCase/backtick extraction would otherwise promote
# into meaningless graph edges.
_TERM_NOISE = {
    "readme", "todo", "true", "false", "none", "null", "yaml", "json",
    "http", "https", "localhost", "github", "markdown", "python3",
}

_alias_groups: dict[str, list[str]] | None = None


def load_alias_map() -> dict[str, list[str]]:
    """
    entity_aliases.yaml maps canonical → [aliases]. Returns a bidirectional
    lookup: every name in a group maps to the other names in its group.
    """
    global _alias_groups
    if _alias_groups is not None:
        return _alias_groups
    groups: dict[str, list[str]] = {}
    if ALIAS_PATH.exists():
        try:
            raw = yaml.safe_load(ALIAS_PATH.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            raw = {}
        for canonical, aliases in raw.items():
            if str(canonical).startswith("_"):
                continue  # underscore keys are config (e.g. _host_domains)
            members = [normalize_entity_name(canonical)]
            members += [normalize_entity_name(a) for a in frontmatter_values(aliases)]
            members = [m for m in members if m]
            for m in members:
                others = [o for o in members if o != m]
                if others:
                    groups.setdefault(m, []).extend(o for o in others if o not in groups.get(m, []))
    _alias_groups = groups
    return groups


def load_known_vocabulary(conn: sqlite3.Connection) -> set[str]:
    """Known single-token names worth matching in chunk content: existing
    entities, _state.yaml top-level keys, and alias-map terms."""
    vocab: set[str] = set()
    try:
        vocab.update(
            name for (name,) in conn.execute("SELECT name FROM entities").fetchall()
            if name and " " not in name
        )
    except sqlite3.OperationalError:
        pass
    state_path = AIKB_ROOT / "_state.yaml"
    if state_path.exists():
        try:
            for m in re.finditer(r"(?m)^([A-Za-z_][A-Za-z0-9_]*):", state_path.read_text(encoding="utf-8")):
                name = normalize_entity_name(m.group(1))
                if name:
                    vocab.add(name)
        except Exception:
            pass
    for name, others in load_alias_map().items():
        vocab.add(name)
        vocab.update(others)
    return {v for v in vocab if len(v) >= 3 and not v.isdigit()}


def content_entities(text: str, vocab: set[str]) -> list[tuple[str, str]]:
    """
    Deterministic entity extraction from chunk text. Capped and
    priority-ordered (host > path/file > ip > term > port) so noisy
    categories can't crowd out strong ones.
    """
    if not text:
        return []

    hosts: list[str] = []
    for m in _host_re().finditer(text):
        name = normalize_entity_name(m.group(1))
        if name:
            hosts.append(name)

    paths: list[tuple[str, str]] = []
    for m in _PATH_RE.finditer(text):
        full = m.group(1)
        name = normalize_entity_name(full)
        if name:
            paths.append((name, "path"))
        stem = normalize_entity_name(Path(full).stem)
        if stem:
            paths.append((stem, "file"))

    ips: list[str] = []
    for m in _IP_RE.finditer(text):
        octets = m.group(1).split(".")
        if all(int(o) <= 255 for o in octets):
            ips.append(m.group(1))

    terms: list[str] = []
    for m in _BACKTICK_RE.finditer(text):
        raw = m.group(1)
        # Backticked filenames also contribute their stem.
        if "/" in raw or "." in raw:
            stem = normalize_entity_name(Path(raw).stem)
            if stem and stem not in _TERM_NOISE:
                terms.append(stem)
        name = normalize_entity_name(raw)
        if name and name not in _TERM_NOISE and not name.isdigit():
            terms.append(name)
    for m in _CAMEL_RE.finditer(text):
        name = normalize_entity_name(m.group(1))
        if name and name not in _TERM_NOISE:
            terms.append(name)
    if vocab:
        words = set(_WORD_RE.findall(text.lower().replace("_", "-")))
        terms.extend(sorted(vocab & words - _TERM_NOISE))

    ports = [m.group(1) for m in _PORT_RE.finditer(text)]

    ordered: list[tuple[str, str]] = []
    ordered += [(h, "host") for h in hosts]
    ordered += paths
    ordered += [(ip, "ip") for ip in ips]
    ordered += [(t, "term") for t in terms]
    ordered += [(p, "port") for p in ports]

    seen: set[tuple[str, str]] = set()
    unique: list[tuple[str, str]] = []
    for name, kind in ordered:
        key = (name, kind)
        if key in seen:
            continue
        seen.add(key)
        unique.append((name, kind))
        if len(unique) >= 12:
            break
    return unique


def chunk_file(file_path: Path, vocab: set[str] | None = None) -> list[dict]:
    """
    Split a markdown file into section-level chunks.

    Each chunk contains:
        file_path   — relative path from AIKB root
        section     — H2 heading text (or "overview" for the preamble)
        content     — first 600 chars of section body (stored as excerpt)
        embed_text  — heading + full body truncated to 2000 chars (used for embedding)
        tags        — space-separated tags from YAML frontmatter
        mtime       — file modification time (for incremental rebuild)
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    fm, body = parse_frontmatter(text)
    rel_path = str(file_path.relative_to(AIKB_ROOT))
    mtime    = file_path.stat().st_mtime
    entities = file_entities(file_path, fm)
    host_names = [name for name, kind in entities if kind == "host"]
    tag_parts = [str(t) for t in fm.get("tags", [])]
    tag_parts.extend(f"host:{name}" for name in host_names)
    tags = " ".join(tag_parts)

    # Split on H2 headings (## ), preserving the heading in each section
    parts = re.split(r"(?m)^(?=## )", body)

    chunks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        lines = part.splitlines()
        if lines[0].startswith("## "):
            heading = lines[0][3:].strip()
            body_text = "\n".join(lines[1:]).strip()
        else:
            heading   = "overview"
            body_text = part

        # Skip near-empty sections (likely just a heading with no content)
        if len(body_text) < 40:
            continue

        embed_text = f"{heading}\n{body_text}"[:2000]

        chunks.append({
            "file_path":  rel_path,
            "section":    heading,
            "content":    body_text[:600],
            "embed_text": embed_text,
            "tags":       tags,
            "mtime":      mtime,
            "entities":   entities + content_entities(embed_text, vocab or set()),
        })

    return chunks

# ── Database ───────────────────────────────────────────────────────────────────

def init_db(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chunks (
            id        INTEGER PRIMARY KEY,
            file_path TEXT    NOT NULL,
            section   TEXT    NOT NULL,
            content   TEXT    NOT NULL,
            tags      TEXT    NOT NULL DEFAULT '',
            mtime     REAL    NOT NULL,
            embedding BLOB    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS file_mtimes (
            file_path TEXT PRIMARY KEY,
            mtime     REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS entities (
            id   INTEGER PRIMARY KEY,
            name TEXT UNIQUE COLLATE NOCASE,
            kind TEXT
        );

        CREATE TABLE IF NOT EXISTS entity_chunks (
            entity_id INTEGER,
            chunk_id  INTEGER,
            PRIMARY KEY(entity_id, chunk_id)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(
                content,
                tags,
                section,
                file_path UNINDEXED
            );
    """)
    # Usage-signal tables (access_stats / feedback_stats / usage_meta) are
    # keyed on (file_path, section), not chunk rowid — rowids churn on reindex.
    from usage_stats import SCHEMA as USAGE_SCHEMA
    conn.executescript(USAGE_SCHEMA)
    conn.commit()


def delete_file(conn: sqlite3.Connection, rel_path: str):
    """Remove all chunks for a file (called before reindexing)."""
    rows = conn.execute(
        "SELECT id FROM chunks WHERE file_path = ?", (rel_path,)
    ).fetchall()
    for (row_id,) in rows:
        conn.execute("DELETE FROM chunks_fts WHERE rowid = ?", (row_id,))
        conn.execute("DELETE FROM entity_chunks WHERE chunk_id = ?", (row_id,))
    conn.execute("DELETE FROM chunks WHERE file_path = ?", (rel_path,))
    conn.execute("DELETE FROM file_mtimes WHERE file_path = ?", (rel_path,))


# Kind precision hierarchy for entity upserts — higher rank wins the name.
_KIND_RANK = {"host": 6, "file": 5, "path": 5, "ip": 4, "alias": 3, "tag": 2, "term": 1, "port": 0}


def insert_entity_links(conn: sqlite3.Connection, chunk_id: int, entities: list[tuple[str, str]]):
    # Alias-group members get linked to the same chunks (kind 'alias') so
    # e.g. "grafana" reaches chunks that only say "ix-grafana".
    alias_groups = load_alias_map()
    if alias_groups:
        expanded = list(entities)
        seen = {name for name, _ in entities}
        for name, _ in entities:
            for other in alias_groups.get(name, ()):
                if other not in seen:
                    seen.add(other)
                    expanded.append((other, "alias"))
        entities = expanded
    for name, kind in entities:
        row = conn.execute(
            "SELECT id, kind FROM entities WHERE name = ? COLLATE NOCASE",
            (name,),
        ).fetchone()
        if row is None:
            cursor = conn.execute(
                "INSERT INTO entities (name, kind) VALUES (?, ?)", (name, kind)
            )
            entity_id = cursor.lastrowid
        else:
            entity_id, existing_kind = row
            # A name keeps its most precise kind: a file stem stays a file
            # even if the same word later shows up as a content term.
            if _KIND_RANK.get(kind, 0) > _KIND_RANK.get(existing_kind, 0):
                conn.execute(
                    "UPDATE entities SET kind = ? WHERE id = ?", (kind, entity_id)
                )
        conn.execute(
            "INSERT OR IGNORE INTO entity_chunks (entity_id, chunk_id) VALUES (?, ?)",
            (entity_id, chunk_id),
        )


def insert_chunks(conn: sqlite3.Connection, chunks: list[dict], embeddings: list[np.ndarray]):
    for chunk, emb in zip(chunks, embeddings):
        emb_bytes = emb.astype(np.float32).tobytes()
        cursor = conn.execute(
            """INSERT INTO chunks (file_path, section, content, tags, mtime, embedding)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (chunk["file_path"], chunk["section"], chunk["content"],
             chunk["tags"], chunk["mtime"], emb_bytes),
        )
        row_id = cursor.lastrowid
        # FTS gets the full embed_text (up to 2000 chars), not the 600-char
        # display excerpt — otherwise BM25 is blind to anything deeper in a
        # section (e.g. an endpoint list below a long preamble).
        conn.execute(
            "INSERT INTO chunks_fts (rowid, content, tags, section, file_path) VALUES (?, ?, ?, ?, ?)",
            (row_id, chunk.get("embed_text", chunk["content"]), chunk["tags"], chunk["section"], chunk["file_path"]),
        )
        insert_entity_links(conn, row_id, chunk.get("entities", []))

    if chunks:
        conn.execute(
            "INSERT OR REPLACE INTO file_mtimes (file_path, mtime) VALUES (?, ?)",
            (chunks[0]["file_path"], chunks[0]["mtime"]),
        )


def index_events(conn: sqlite3.Connection, force: bool = False, verbose: bool = True):
    """
    Index _runtime/events/YYYY-MM-DD.ndjson files.
    Each event becomes a chunk.
    """
    events_dir = AIKB_ROOT / "_runtime" / "events"
    if not events_dir.exists():
        return

    cached_mtimes = dict(
        conn.execute(
            "SELECT file_path, mtime FROM file_mtimes WHERE file_path LIKE '_runtime/events/%'"
        ).fetchall()
    )

    ndjson_files = sorted(events_dir.glob("*.ndjson"))
    now = datetime.now()

    files_to_index = []
    for f in ndjson_files:
        rel = str(f.relative_to(AIKB_ROOT))

        # Skip raw logs > 14 days old if compacted counterpart exists
        try:
            f_date = datetime.strptime(f.stem, "%Y-%m-%d")
            age_days = (now - f_date).days
            if age_days > 14:
                compacted_file = events_dir / "compacted" / f"{f.stem}.json"
                if compacted_file.exists():
                    # Prune if previously indexed
                    if rel in cached_mtimes:
                        if verbose:
                            print(f"  Pruning stale raw event log: {rel} (compacted exists)")
                        delete_file(conn, rel)
                    continue
        except ValueError:
            pass

        current_mtime = f.stat().st_mtime
        if not force and cached_mtimes.get(rel) == current_mtime:
            continue
        files_to_index.append(f)

    if not files_to_index:
        return

    if verbose:
        print(f"Indexing {len(files_to_index)} event log(s)...")

    vocab = load_known_vocabulary(conn)
    for f in files_to_index:
        rel = str(f.relative_to(AIKB_ROOT))
        delete_file(conn, rel)

        chunks = []
        try:
            with f.open("r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        ts_utc  = event.get("ts_utc", "")
                        summary = event.get("summary", "")
                        agent   = event.get("agent", "unknown")
                        etype   = event.get("type", "event")
                        project = event.get("project", "")
                        rejected = event.get("rejected", "")
                        assumptions = event.get("assumptions", "")
                        invariants = event.get("invariants", "")
                        next_step = event.get("next_step", "")

                        content_parts = [f"[{agent}] {summary}"]
                        embed_parts = [f"Event {etype} by {agent} for {project}: {summary}"]

                        if rejected:
                            content_parts.append(f"Rejected: {rejected}")
                            embed_parts.append(f"Rejected: {rejected}")
                        if assumptions:
                            content_parts.append(f"Assumptions: {assumptions}")
                            embed_parts.append(f"Assumptions: {assumptions}")
                        if invariants:
                            content_parts.append(f"Invariants: {invariants}")
                            embed_parts.append(f"Invariants: {invariants}")
                        if next_step:
                            content_parts.append(f"Next step: {next_step}")
                            embed_parts.append(f"Next step: {next_step}")

                        content_full = "\n".join(content_parts)
                        embed_full = "\n".join(embed_parts)

                        # Parse ts_utc to unix timestamp
                        try:
                            # 2026-04-13T12:34:56Z -> iso format
                            ds = ts_utc.replace("Z", "+00:00")
                            dt = datetime.fromisoformat(ds)
                            mtime = dt.timestamp()
                        except:
                            mtime = f.stat().st_mtime

                        chunks.append({
                            "file_path":  rel,
                            "section":    f"{etype} @ {ts_utc}",
                            "content":    content_full[:800],
                            "embed_text": embed_full[:2000],
                            "tags":       f"event {etype} {agent} memory {project}",
                            "mtime":      mtime,
                            "entities":   content_entities(embed_full[:2000], vocab),
                        })
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            if verbose:
                print(f"  Error reading {rel}: {e}")
            continue

        if not chunks:
            # Still record the mtime so we don't re-scan an empty/broken file
            conn.execute(
                "INSERT OR REPLACE INTO file_mtimes (file_path, mtime) VALUES (?, ?)",
                (rel, f.stat().st_mtime),
            )
            continue

        texts      = [c["embed_text"] for c in chunks]
        embeddings = embed(texts)

        insert_chunks(conn, chunks, embeddings)
        # Ensure file_mtimes records the actual file mtime so incremental check works
        conn.execute(
            "INSERT OR REPLACE INTO file_mtimes (file_path, mtime) VALUES (?, ?)",
            (rel, f.stat().st_mtime),
        )

        if verbose:
            print(f"  {rel} → {len(chunks)} event(s)")

def index_compacted(conn: sqlite3.Connection, force: bool = False, verbose: bool = True):
    """
    Index _runtime/events/compacted/YYYY-MM-DD.json summary files.
    """
    compacted_dir = AIKB_ROOT / "_runtime" / "events" / "compacted"
    if not compacted_dir.exists():
        return

    cached_mtimes = dict(
        conn.execute(
            "SELECT file_path, mtime FROM file_mtimes WHERE file_path LIKE '_runtime/events/compacted/%'"
        ).fetchall()
    )

    json_files = sorted(compacted_dir.glob("*.json"))

    files_to_index = []
    for f in json_files:
        rel = str(f.relative_to(AIKB_ROOT))
        current_mtime = f.stat().st_mtime
        if not force and cached_mtimes.get(rel) == current_mtime:
            continue
        files_to_index.append(f)

    if not files_to_index:
        return

    if verbose:
        print(f"Indexing {len(files_to_index)} compacted event summary(s)...")

    vocab = load_known_vocabulary(conn)
    for f in files_to_index:
        rel = str(f.relative_to(AIKB_ROOT))
        delete_file(conn, rel)

        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            if verbose:
                print(f"  Error reading {rel}: {e}")
            continue

        date_str = f.stem
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            mtime = dt.timestamp()
        except:
            mtime = f.stat().st_mtime

        chunks = []
        if data.get("version") == 2 and data.get("observations"):
            # v2: one chunk per (project, date) with dated fact bullets —
            # compacted months stay searchable as dated facts, not prose.
            by_project: dict[str, list[dict]] = {}
            for obs in data["observations"]:
                by_project.setdefault(obs.get("project", "unknown"), []).append(obs)
            for project, obs_list in sorted(by_project.items()):
                parts = [f"Observations for {project} on {date_str}:"]
                types = sorted({o.get("type", "") for o in obs_list})
                for obs in obs_list:
                    parts.append(f"\n{obs.get('type', 'observation')}:")
                    for fact in obs.get("facts", []):
                        parts.append(f"- [{date_str}] {fact}")
                content_full = "\n".join(parts)
                chunks.append({
                    "file_path":  rel,
                    "section":    f"{project} @ {date_str}",
                    "content":    content_full[:800],
                    "embed_text": content_full[:2000],
                    "tags":       f"event compacted memory observation {project} {' '.join(types)}",
                    "mtime":      mtime,
                    "entities":   content_entities(content_full[:2000], vocab)
                                  + ([(n, "term")] if (n := normalize_entity_name(project)) else []),
                })
        else:
            # v1 fallback: existing highlight rendering, one chunk per file.
            content_parts = [f"Compacted events from {date_str} ({data.get('event_count', 0)} events)"]
            highlights = data.get("highlights", {})
            for project, items in highlights.items():
                content_parts.append(f"\n## {project}")
                for item in items:
                    content_parts.append(f"- {item}")
            content_full = "\n".join(content_parts)
            chunks.append({
                "file_path":  rel,
                "section":    f"compacted @ {date_str}",
                "content":    content_full[:800],
                "embed_text": content_full[:2000],
                "tags":       "event compacted memory",
                "mtime":      mtime,
                "entities":   content_entities(content_full[:2000], vocab),
            })

        insert_chunks(conn, chunks, embed([c["embed_text"] for c in chunks]))
        # Ensure file_mtimes records actual st_mtime for incremental logic
        conn.execute(
            "INSERT OR REPLACE INTO file_mtimes (file_path, mtime) VALUES (?, ?)",
            (rel, f.stat().st_mtime),
        )

        if verbose:
            print(f"  {rel} → {len(chunks)} compacted chunk(s)")

def index_scripts(conn: sqlite3.Connection, force: bool = False, verbose: bool = True):
    """
    Index _tools/**/*.py and *.sh script headers (docstring/leading comments)
    so "where is the script that does X" queries can resolve to tooling.
    """
    tools_dir = AIKB_ROOT / "_tools"
    if not tools_dir.exists():
        return

    cached_mtimes = dict(
        conn.execute(
            "SELECT file_path, mtime FROM file_mtimes WHERE file_path LIKE '_tools/%'"
        ).fetchall()
    )

    vocab = load_known_vocabulary(conn)
    indexed = 0
    for f in sorted(tools_dir.rglob("*")):
        if f.suffix not in {".py", ".sh"} or not f.is_file():
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue

        rel = str(f.relative_to(AIKB_ROOT))
        mtime = f.stat().st_mtime
        if not force and cached_mtimes.get(rel) == mtime:
            continue

        try:
            head = f.read_text(encoding="utf-8", errors="replace")[:2000]
        except Exception:
            continue
        if len(head.strip()) < 40:
            continue

        delete_file(conn, rel)
        lang = "python" if f.suffix == ".py" else "shell"
        stem = normalize_entity_name(f.stem)
        script_entities = ([(stem, "file")] if stem else []) + content_entities(head, vocab)
        chunk = {
            "file_path":  rel,
            "section":    "script",
            "content":    head[:800],
            "embed_text": f"{f.name} {lang} script\n{head}"[:2000],
            "tags":       f"script tool cli {lang}",
            "mtime":      mtime,
            "entities":   script_entities,
        }
        insert_chunks(conn, [chunk], embed([chunk["embed_text"]]))
        indexed += 1

    if indexed and verbose:
        print(f"  _tools scripts → {indexed} file(s)")


def index_candidates(conn: sqlite3.Connection, force: bool = False, verbose: bool = True):
    """
    Index _runtime/candidates/YYYY-MM-DD.yaml promotion-candidate files,
    one chunk per file.
    """
    cand_dir = AIKB_ROOT / "_runtime" / "candidates"
    if not cand_dir.exists():
        return

    cached_mtimes = dict(
        conn.execute(
            "SELECT file_path, mtime FROM file_mtimes WHERE file_path LIKE '_runtime/candidates/%'"
        ).fetchall()
    )

    vocab = load_known_vocabulary(conn)
    indexed = 0
    for f in sorted(cand_dir.glob("*.yaml")):
        rel = str(f.relative_to(AIKB_ROOT))
        mtime = f.stat().st_mtime
        if not force and cached_mtimes.get(rel) == mtime:
            continue

        try:
            text = f.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        if len(text) < 30:
            continue

        delete_file(conn, rel)
        chunk = {
            "file_path":  rel,
            "section":    f"candidates {f.stem}",
            "content":    text[:800],
            "embed_text": f"promotion candidates {f.stem}\n{text}"[:2000],
            "tags":       "candidates promotion memory runtime",
            "mtime":      mtime,
            "entities":   content_entities(text[:2000], vocab),
        }
        insert_chunks(conn, [chunk], embed([chunk["embed_text"]]))
        indexed += 1

    if indexed and verbose:
        print(f"  _runtime/candidates → {indexed} file(s)")


# ── Index builder ──────────────────────────────────────────────────────────────

def chunk_state_yaml() -> list[dict]:
    """
    Index _state.yaml by its top-level YAML keys (pending, ssl_certs,
    open_incidents, recently_changed, ...) so each category is
    independently searchable.
    """
    state_path = AIKB_ROOT / "_state.yaml"
    if not state_path.exists():
        return []

    text  = state_path.read_text(encoding="utf-8")
    mtime = state_path.stat().st_mtime

    # Split before each top-level key (column-0 identifier followed by ':').
    sections = re.split(r"\n(?=[A-Za-z_][A-Za-z0-9_]*:)", text)
    chunks = []

    for section in sections:
        section = section.strip()
        if not section or len(section) < 30:
            continue

        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*):", section)
        heading = m.group(1).replace("_", " ") if m else "state-overview"

        # Window long categories (e.g. pending: with dozens of items) so
        # entries past the first 2000 chars stay searchable.
        windows = [section[i:i + 1900] for i in range(0, len(section), 1900)]
        for idx, window in enumerate(windows):
            chunks.append({
                "file_path":  "_state.yaml",
                "section":    heading if idx == 0 else f"{heading} (part {idx + 1})",
                "content":    window[:800],
                "embed_text": f"{heading}\n{window}"[:2000],
                "tags":       "state incidents pending blockers ssl expiry open blocked waiting",
                "mtime":      mtime,
            })

    if not chunks:
        chunks = [{
            "file_path":  "_state.yaml",
            "section":    "state",
            "content":    text[:800],
            "embed_text": text[:2000],
            "tags":       "state incidents pending ssl expiry open blocked",
            "mtime":      mtime,
        }]

    return chunks


def prune_high_degree_entities(conn: sqlite3.Connection, max_degree: int = 300):
    """
    Drop links for content-derived entities attached to too many chunks —
    a term linked to 300+ chunks ("python", "docker") is a universal edge
    that adds noise, not signal. Hosts/files/tags are kept regardless.
    """
    conn.execute(
        """DELETE FROM entity_chunks WHERE entity_id IN (
               SELECT e.id FROM entities e
               JOIN entity_chunks ec ON ec.entity_id = e.id
               WHERE e.kind IN ('term', 'term-llm', 'alias', 'port', 'ip')
               GROUP BY e.id
               HAVING COUNT(*) > ?
           )""",
        (max_degree,),
    )


def build_index(force: bool = False, verbose: bool = True):
    """
    Walk AIKB and index any .md file (+ _state.yaml) that is new or modified.
    Pass force=True to reindex everything regardless of mtime.
    """
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    cached_mtimes = dict(
        conn.execute("SELECT file_path, mtime FROM file_mtimes").fetchall()
    )

    md_files = sorted(
        p for p in AIKB_ROOT.rglob("*.md")
        if not any(skip in p.parts for skip in SKIP_DIRS)
        and not SKIP_FILE_RE.search(p.name)
    )

    files_to_index = []
    for f in md_files:
        rel = str(f.relative_to(AIKB_ROOT))
        current_mtime = f.stat().st_mtime
        if not force and cached_mtimes.get(rel) == current_mtime:
            continue
        files_to_index.append(f)

    state_path = AIKB_ROOT / "_state.yaml"
    state_rel  = "_state.yaml"
    if state_path.exists():
        state_mtime = state_path.stat().st_mtime
        if force or cached_mtimes.get(state_rel) != state_mtime:
            files_to_index.append(None)  # sentinel for state yaml

    if not files_to_index:
        # Check for events/candidates/scripts even if md files are up to date
        index_events(conn, force=force, verbose=verbose)
        index_compacted(conn, force=force, verbose=verbose)
        index_candidates(conn, force=force, verbose=verbose)
        index_scripts(conn, force=force, verbose=verbose)
        prune_high_degree_entities(conn)
        from usage_stats import refresh_feedback_stats, refresh_usage_stats
        refresh_usage_stats(conn)
        refresh_feedback_stats(conn)
        conn.commit()
        conn.close()
        return

    if verbose:
        print(f"Indexing {len(files_to_index)} source(s)...")

    vocab = load_known_vocabulary(conn)
    total_chunks = 0
    for f in files_to_index:
        if f is None:
            chunks = chunk_state_yaml()
            rel = "_state.yaml"
        else:
            rel    = str(f.relative_to(AIKB_ROOT))
            chunks = chunk_file(f, vocab)

        if not chunks:
            continue

        delete_file(conn, rel)

        texts      = [c["embed_text"] for c in chunks]
        embeddings = embed(texts)

        insert_chunks(conn, chunks, embeddings)
        total_chunks += len(chunks)

        if verbose:
            print(f"  {rel} → {len(chunks)} chunk(s)")

    # ── 3. Events + candidates + scripts ──────────────────────────────────────
    index_events(conn, force=force, verbose=verbose)
    index_compacted(conn, force=force, verbose=verbose)
    index_candidates(conn, force=force, verbose=verbose)
    index_scripts(conn, force=force, verbose=verbose)

    prune_high_degree_entities(conn)
    from usage_stats import refresh_feedback_stats, refresh_usage_stats
    refresh_usage_stats(conn)
    refresh_feedback_stats(conn)
    conn.commit()
    conn.close()

    if verbose:
        print(f"Done. {total_chunks} chunk(s) indexed across {len(files_to_index)} file(s).")
        print(f"Index: {DB_PATH}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    build_index(force=force)

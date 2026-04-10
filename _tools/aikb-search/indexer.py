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

import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import yaml

# ── Paths ──────────────────────────────────────────────────────────────────────
TOOL_DIR  = Path(__file__).parent
AIKB_ROOT = TOOL_DIR.parent.parent          # _tools/aikb-search/ → AIKB/
DB_PATH   = TOOL_DIR / "aikb_index.db"

# Directories to skip when walking AIKB
SKIP_DIRS = {"_tools", "_agents", "_templates", ".git"}

# ── Embedding (lazy singleton) ─────────────────────────────────────────────────
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        # Downloads ~23 MB on first use, cached in ~/.cache/fastembed/
        _embedder = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    return _embedder

def embed(texts: list[str]) -> list[np.ndarray]:
    """Return list of float32 unit vectors, one per text."""
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


def chunk_file(file_path: Path) -> list[dict]:
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
    tags     = " ".join(str(t) for t in fm.get("tags", []))
    mtime    = file_path.stat().st_mtime

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

        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(
                content,
                tags,
                section,
                file_path UNINDEXED
            );
    """)
    conn.commit()


def delete_file(conn: sqlite3.Connection, rel_path: str):
    """Remove all chunks for a file (called before reindexing)."""
    rows = conn.execute(
        "SELECT id FROM chunks WHERE file_path = ?", (rel_path,)
    ).fetchall()
    for (row_id,) in rows:
        conn.execute("DELETE FROM chunks_fts WHERE rowid = ?", (row_id,))
    conn.execute("DELETE FROM chunks WHERE file_path = ?", (rel_path,))
    conn.execute("DELETE FROM file_mtimes WHERE file_path = ?", (rel_path,))


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
        conn.execute(
            "INSERT INTO chunks_fts (rowid, content, tags, section, file_path) VALUES (?, ?, ?, ?, ?)",
            (row_id, chunk["content"], chunk["tags"], chunk["section"], chunk["file_path"]),
        )

    if chunks:
        conn.execute(
            "INSERT OR REPLACE INTO file_mtimes (file_path, mtime) VALUES (?, ?)",
            (chunks[0]["file_path"], chunks[0]["mtime"]),
        )

# ── Index builder ──────────────────────────────────────────────────────────────

def chunk_state_yaml() -> list[dict]:
    """
    Index _state.yaml by its top-level sections (split on '# ───' markers)
    so each category (SSL certs, pending, incidents, recent changes) is
    independently searchable.
    """
    state_path = AIKB_ROOT / "_state.yaml"
    if not state_path.exists():
        return []

    text  = state_path.read_text(encoding="utf-8")
    mtime = state_path.stat().st_mtime

    sections = re.split(r'\n(?=# ─+)', text)
    chunks = []

    for section in sections:
        section = section.strip()
        if not section or len(section) < 30:
            continue

        first_line = section.splitlines()[0]
        heading = re.sub(r'^#\s*─+\s*', '', first_line).strip()
        if not heading:
            heading = "state-overview"

        chunks.append({
            "file_path":  "_state.yaml",
            "section":    heading,
            "content":    section[:800],
            "embed_text": section[:2000],
            "tags":       "state incidents pending ssl expiry open blocked",
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
        if verbose:
            print("Index up to date — nothing to do.")
        conn.close()
        return

    if verbose:
        print(f"Indexing {len(files_to_index)} source(s)...")

    total_chunks = 0
    for f in files_to_index:
        if f is None:
            chunks = chunk_state_yaml()
            rel = "_state.yaml"
        else:
            rel    = str(f.relative_to(AIKB_ROOT))
            chunks = chunk_file(f)

        if not chunks:
            continue

        delete_file(conn, rel)

        texts      = [c["embed_text"] for c in chunks]
        embeddings = embed(texts)

        insert_chunks(conn, chunks, embeddings)
        total_chunks += len(chunks)

        if verbose:
            print(f"  {rel} → {len(chunks)} chunk(s)")

    conn.commit()
    conn.close()

    if verbose:
        print(f"Done. {total_chunks} chunk(s) indexed across {len(files_to_index)} file(s).")
        print(f"Index: {DB_PATH}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    build_index(force=force)

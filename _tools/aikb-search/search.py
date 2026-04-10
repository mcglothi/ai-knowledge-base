"""
AIKB Search

Hybrid retrieval: BM25 (SQLite FTS5) + cosine similarity (numpy),
merged with Reciprocal Rank Fusion (RRF).

For 50–500 chunks, loading all embeddings into numpy at query time is
~1ms — no ANN index needed. The FTS5 keyword search handles exact
matches (hostnames, IPs, error strings); vector similarity handles
semantic matches; RRF merges both without tuning weights.
"""

import re
import sqlite3
from pathlib import Path

import numpy as np

from indexer import DB_PATH, embed

# ── Helpers ────────────────────────────────────────────────────────────────────

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "and", "or", "but", "if", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "up", "about", "into", "through", "during", "before",
    "after", "above", "below", "between", "out", "off", "over", "under",
    "then", "than", "so", "yet", "both", "either", "neither", "not",
    "no", "nor", "as", "at", "that", "this", "it", "its", "i", "my",
    "me", "you", "your", "he", "she", "we", "they", "their", "them",
    "soon", "now", "just", "also", "get", "any", "all", "there",
}


def fts_safe(query: str) -> str:
    """
    Sanitize a query for FTS5 MATCH.
    Strips stopwords and FTS5 special characters, then ORs the remaining
    meaningful terms so any row containing any term gets a BM25 score.
    OR logic casts a wide net; BM25 ranking handles precision.
    """
    words = [w.lower() for w in re.findall(r'\w+', query)]
    terms = [w for w in words if w not in _STOPWORDS and len(w) > 1]
    if not terms:
        # Fallback: use all words if stopword filtering left nothing
        terms = [w for w in words if len(w) > 1]
    if not terms:
        return '""'
    return " OR ".join(f'"{t}"' for t in terms)


def rrf(rankings: list[dict[int, int]], k: int = 60) -> dict[int, float]:
    """
    Reciprocal Rank Fusion over multiple ranked lists.

    rankings: list of {chunk_id: rank} dicts (rank is 1-based)
    Returns {chunk_id: combined_score} — higher is better.
    """
    scores: dict[int, float] = {}
    for ranking in rankings:
        for chunk_id, rank in ranking.items():
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores


# ── Search ─────────────────────────────────────────────────────────────────────

def search(query: str, top_k: int = 5, db_path: Path = DB_PATH) -> list[dict]:
    """
    Search AIKB for content relevant to query.

    Returns list of dicts:
        file     — relative path from AIKB root
        section  — H2 heading (or "overview")
        excerpt  — first ~300 chars of section body
        score    — RRF score (higher = more relevant, not bounded to [0,1])
        sources  — which retrieval methods matched ("bm25", "vector", or "both")
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"Index not found at {db_path}. Run: python3 indexer.py"
        )

    conn = sqlite3.connect(db_path)

    # ── 1. BM25 via FTS5 ──────────────────────────────────────────────────────
    bm25_ranks: dict[int, int] = {}
    try:
        safe_q = fts_safe(query)
        rows = conn.execute(
            "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT 60",
            (safe_q,),
        ).fetchall()
        bm25_ranks = {row[0]: i + 1 for i, row in enumerate(rows)}
    except sqlite3.OperationalError:
        # FTS5 parse error — skip BM25 for this query
        pass

    # ── 2. Vector cosine similarity ───────────────────────────────────────────
    rows = conn.execute("SELECT id, embedding FROM chunks").fetchall()
    conn.close()

    vec_ranks: dict[int, int] = {}
    if rows:
        ids  = [r[0] for r in rows]
        embs = np.array(
            [np.frombuffer(r[1], dtype=np.float32) for r in rows]
        )  # shape: (N, 384)

        q_emb = embed([query])[0].astype(np.float32)  # shape: (384,)

        # Normalised dot product = cosine similarity
        norms  = np.linalg.norm(embs, axis=1)
        q_norm = np.linalg.norm(q_emb)
        with np.errstate(divide="ignore", invalid="ignore"):
            sims = np.where(
                (norms > 0) & (q_norm > 0),
                (embs @ q_emb) / (norms * q_norm),
                0.0,
            )

        top_idx  = np.argsort(sims)[::-1][:60]
        vec_ranks = {ids[i]: rank + 1 for rank, i in enumerate(top_idx)}

    # ── 3. RRF merge ──────────────────────────────────────────────────────────
    combined = rrf([bm25_ranks, vec_ranks])
    top_ids  = sorted(combined, key=combined.__getitem__, reverse=True)[:top_k]

    if not top_ids:
        return []

    # ── 4. Fetch results ──────────────────────────────────────────────────────
    conn = sqlite3.connect(db_path)
    results = []
    for chunk_id in top_ids:
        row = conn.execute(
            "SELECT file_path, section, content FROM chunks WHERE id = ?",
            (chunk_id,),
        ).fetchone()
        if not row:
            continue

        in_bm25  = chunk_id in bm25_ranks
        in_vec   = chunk_id in vec_ranks
        sources  = "both" if (in_bm25 and in_vec) else ("bm25" if in_bm25 else "vector")

        results.append({
            "file":    row[0],
            "section": row[1],
            "excerpt": row[2][:350].replace("\n", " ").strip(),
            "score":   round(combined[chunk_id], 4),
            "sources": sources,
        })

    conn.close()
    return results


def format_results(results: list[dict]) -> str:
    """Format search results for display in Claude's context."""
    if not results:
        return "No results found."

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['file']} § {r['section']}  ({r['sources']}, score {r['score']})")
        lines.append(f"    {r['excerpt']}")
        lines.append("")

    return "\n".join(lines).rstrip()

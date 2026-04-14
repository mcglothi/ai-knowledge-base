"""
AIKB Search

Hybrid retrieval: BM25 (SQLite FTS5) + cosine similarity (numpy),
with optional relationship expansion and temporal reasoning.

- BM25 handles exact tokens (hostnames, IPs, error strings)
- Vector similarity handles semantic matches
- Graph expansion surfaces related chunks across domains
- Temporal reasoning supports recency-boosting and historical snapshots
"""

from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from indexer import DB_PATH, embed

# ── Helpers ────────────────────────────────────────────────────────────────────

def recency_boost(mtime: float) -> float:
    """Return a score boost in [0, 2.0] that decays linearly over 14 days."""
    age_days = (time.time() - mtime) / 86400
    if age_days >= 14:
        return 0.0
    return round(2.0 * (1.0 - age_days / 14), 3)


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

_REL_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_.:/-]{2,}")
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


@dataclass
class TemporalConstraint:
    cleaned_query: str
    as_of: datetime | None = None
    before: datetime | None = None
    after: datetime | None = None


def _parse_ymd(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _strip_temporal_phrases(query: str) -> tuple[str, TemporalConstraint]:
    cleaned = query
    as_of = None
    before = None
    after = None

    patterns = [
        (r"\bbetween\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})\b", "between"),
        (r"\bas\s+of\s+(\d{4}-\d{2}-\d{2})\b", "as_of"),
        (r"\bbefore\s+(\d{4}-\d{2}-\d{2})\b", "before"),
        (r"\b(after|since)\s+(\d{4}-\d{2}-\d{2})\b", "after"),
    ]

    for pattern, kind in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if not match:
            continue
        if kind == "between":
            after = _parse_ymd(match.group(1))
            before = _parse_ymd(match.group(2))
        elif kind == "as_of":
            as_of = _parse_ymd(match.group(1))
            before = as_of
        elif kind == "before":
            before = _parse_ymd(match.group(1))
        elif kind == "after":
            after = _parse_ymd(match.group(2))
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+", " ", cleaned).strip() or query.strip()
    return cleaned, TemporalConstraint(cleaned_query=cleaned, as_of=as_of, before=before, after=after)


def parse_temporal_query(
    query: str,
    *,
    as_of: str | None = None,
    before: str | None = None,
    after: str | None = None,
) -> TemporalConstraint:
    cleaned, temporal = _strip_temporal_phrases(query)

    explicit_as_of = _parse_ymd(as_of)
    explicit_before = _parse_ymd(before)
    explicit_after = _parse_ymd(after)

    if explicit_as_of:
        temporal.as_of = explicit_as_of
        temporal.before = explicit_as_of
    if explicit_before:
        temporal.before = explicit_before
    if explicit_after:
        temporal.after = explicit_after

    temporal.cleaned_query = cleaned
    return temporal


def extract_chunk_date(content: str, section: str, mtime: float) -> datetime:
    # Prefer explicit date in heading or content.
    for text in (section, content):
        m = _DATE_RE.search(text)
        if m:
            dt = _parse_ymd(m.group(1))
            if dt:
                return dt

    return datetime.fromtimestamp(mtime, tz=timezone.utc)


def within_temporal_window(chunk_dt: datetime, temporal: TemporalConstraint) -> bool:
    if temporal.before and chunk_dt.date() > temporal.before.date():
        return False
    if temporal.after and chunk_dt.date() < temporal.after.date():
        return False
    return True


def temporal_distance_days(chunk_dt: datetime, temporal: TemporalConstraint) -> float:
    if temporal.as_of:
        return abs((temporal.as_of - chunk_dt).total_seconds()) / 86400.0
    if temporal.before:
        return abs((temporal.before - chunk_dt).total_seconds()) / 86400.0
    if temporal.after:
        return abs((chunk_dt - temporal.after).total_seconds()) / 86400.0
    # No explicit temporal target -> favor recency by default.
    return max(0.0, (datetime.now(timezone.utc) - chunk_dt).total_seconds() / 86400.0)


def fts_safe(query: str) -> str:
    """
    Sanitize a query for FTS5 MATCH.
    Strips stopwords and FTS5 special characters, then ORs the remaining
    meaningful terms so any row containing any term gets a BM25 score.
    """
    words = [w.lower() for w in re.findall(r'\w+', query)]
    terms = [w for w in words if w not in _STOPWORDS and len(w) > 1]
    if not terms:
        terms = [w for w in words if len(w) > 1]
    if not terms:
        return '""'
    return " OR ".join(f'"{t}"' for t in terms)


def rrf(rankings: list[dict[int, int]], k: int = 60) -> dict[int, float]:
    """Reciprocal Rank Fusion over multiple ranked lists."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for chunk_id, rank in ranking.items():
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores


def relationship_tokens(*texts: str) -> set[str]:
    toks: set[str] = set()
    for text in texts:
        for tok in _REL_TOKEN_RE.findall(text.lower()):
            if tok in _STOPWORDS:
                continue
            if tok.isdigit():
                continue
            toks.add(tok)
    return toks


def build_graph_ranks(
    chunk_meta: dict[int, dict],
    seed_scores: dict[int, float],
    *,
    max_seeds: int = 12,
    max_df: int = 120,
) -> dict[int, int]:
    """
    Lightweight Graph-RAG expansion based on shared tokens across
    (path, section, tags, content).
    """
    if not chunk_meta or not seed_scores:
        return {}

    sorted_seeds = sorted(seed_scores.items(), key=lambda x: x[1], reverse=True)[:max_seeds]
    seed_ids = [cid for cid, _ in sorted_seeds]

    token_sets: dict[int, set[str]] = {}
    token_to_ids: dict[str, set[int]] = {}
    for cid, row in chunk_meta.items():
        toks = relationship_tokens(row["file_path"], row["section"], row["tags"], row["content"])
        token_sets[cid] = toks
        for tok in toks:
            token_to_ids.setdefault(tok, set()).add(cid)

    graph_scores: dict[int, float] = {}
    for seed_rank, seed_id in enumerate(seed_ids, 1):
        seed_weight = 1.0 / seed_rank
        for tok in token_sets.get(seed_id, set()):
            ids = token_to_ids.get(tok, set())
            df = len(ids)
            if df < 2 or df > max_df:
                continue
            token_weight = 1.0 / (1.0 + np.log1p(df))
            for other_id in ids:
                if other_id == seed_id:
                    continue
                graph_scores[other_id] = graph_scores.get(other_id, 0.0) + (seed_weight * token_weight)

    if not graph_scores:
        return {}

    ranked = sorted(graph_scores.items(), key=lambda x: x[1], reverse=True)[:60]
    return {cid: i + 1 for i, (cid, _) in enumerate(ranked)}


# ── Search ─────────────────────────────────────────────────────────────────────

def search(
    query: str,
    top_k: int = 5,
    db_path: Path = DB_PATH,
    *,
    include_related: bool = True,
    as_of: str | None = None,
    before: str | None = None,
    after: str | None = None,
) -> list[dict]:
    """
    Search AIKB for content relevant to query.

    Returns list of dicts:
        file     — relative path from AIKB root
        section  — H2 heading (or "overview")
        excerpt  — first ~300 chars of section body
        date     — inferred chunk date (YYYY-MM-DD)
        score    — RRF score (higher = more relevant)
        sources  — which retrieval methods matched
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Index not found at {db_path}. Run: python3 indexer.py")

    temporal = parse_temporal_query(query, as_of=as_of, before=before, after=after)
    normalized_query = temporal.cleaned_query

    conn = sqlite3.connect(db_path)

    # 1) BM25 via FTS5
    bm25_ranks: dict[int, int] = {}
    try:
        safe_q = fts_safe(normalized_query)
        rows = conn.execute(
            "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT 60",
            (safe_q,),
        ).fetchall()
        bm25_ranks = {row[0]: i + 1 for i, row in enumerate(rows)}
    except sqlite3.OperationalError:
        pass

    # 2) Load all chunk metadata + embeddings once.
    rows = conn.execute(
        "SELECT id, file_path, section, content, tags, mtime, embedding FROM chunks"
    ).fetchall()
    conn.close()

    if not rows:
        return []

    chunk_meta = {
        r[0]: {
            "file_path": r[1],
            "section": r[2],
            "content": r[3],
            "tags": r[4] or "",
            "mtime": r[5],
            "embedding": r[6],
        }
        for r in rows
    }

    # 3) Vector cosine similarity
    ids = [r[0] for r in rows]
    embs = np.array([np.frombuffer(r[6], dtype=np.float32) for r in rows])

    q_emb = embed([normalized_query])[0].astype(np.float32)

    norms = np.linalg.norm(embs, axis=1)
    q_norm = np.linalg.norm(q_emb)
    with np.errstate(divide="ignore", invalid="ignore"):
        sims = np.where((norms > 0) & (q_norm > 0), (embs @ q_emb) / (norms * q_norm), 0.0)

    top_idx = np.argsort(sims)[::-1][:60]
    vec_ranks = {ids[i]: rank + 1 for rank, i in enumerate(top_idx)}

    # 4) Base RRF
    keyword_scores: dict[int, float] = {}
    prior_scores: dict[int, float] = {}
    q_tokens = relationship_tokens(normalized_query)
    q_words = set(re.findall(r"[a-z0-9_/-]+", normalized_query.lower()))
    is_script_intent = bool(q_words & {"script", "cli", "tool", "python", "server"})
    is_agent_intent = bool(q_words & {"agent", "codex", "gemini", "claude", "cursor", "instructions", "rules"})
    is_memory_intent = bool(q_words & {"memory", "proposal", "heartbeat", "staging", "pipeline", "mcp", "temporal", "graph"})
    q_slug = re.sub(r"[^a-z0-9]+", "-", normalized_query.lower()).strip("-")
    for cid, row in chunk_meta.items():
        fp = row["file_path"].lower()
        section = row["section"].lower()
        tags = (row["tags"] or "").lower()

        s = 0.0
        for tok in q_tokens:
            if tok in fp:
                s += 2.0
            if tok in section:
                s += 1.5
            if tok in tags:
                s += 1.0
        if q_slug and q_slug in fp:
            s += 3.0

        if s > 0:
            keyword_scores[cid] = s

        # Intent-aware priors to reduce false positives in broad corpora.
        p = 0.0
        if is_script_intent and fp.startswith("_tools/"):
            p += 0.08
        if is_agent_intent and fp.startswith("_agents/"):
            p += 0.08
        if is_memory_intent and (
            fp.startswith("_runtime/")
            or fp.startswith("_tools/memory-")
        ):
            p += 0.06
        if p:
            prior_scores[cid] = p

    keyword_ranked = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:60]
    keyword_ranks = {cid: i + 1 for i, (cid, _) in enumerate(keyword_ranked)}

    rankings: list[dict[int, int]] = [bm25_ranks, vec_ranks, keyword_ranks]

    # 5) Relationship expansion (Graph-RAG)
    graph_ranks: dict[int, int] = {}
    if include_related:
        seed_scores = rrf(rankings)
        graph_ranks = build_graph_ranks(chunk_meta, seed_scores)
        rankings.append(graph_ranks)

    # 6) Temporal rank/filt
    temporal_ranks: dict[int, int] = {}
    has_temporal = any((temporal.as_of, temporal.before, temporal.after))

    temporal_candidates: list[tuple[int, float]] = []
    for cid, row in chunk_meta.items():
        dt = extract_chunk_date(row["content"], row["section"], row["mtime"])
        if has_temporal and not within_temporal_window(dt, temporal):
            continue
        temporal_candidates.append((cid, temporal_distance_days(dt, temporal)))

    temporal_candidates.sort(key=lambda x: x[1])
    temporal_ranks = {cid: rank + 1 for rank, (cid, _) in enumerate(temporal_candidates[:120])}
    if has_temporal:
        rankings.append(temporal_ranks)

    combined = rrf(rankings)
    if prior_scores:
        for cid, bonus in prior_scores.items():
            combined[cid] = combined.get(cid, 0.0) + bonus

    # 7) Recency Boost
    for cid in list(combined.keys()):
        row = chunk_meta.get(cid)
        if not row:
            continue
        mtime = row["mtime"]
        fpath = row["file_path"]
        
        boost = recency_boost(mtime)
        # Events can win on recency but docs hold advantage at equal age
        if fpath.startswith("_runtime/events/"):
            boost *= 0.6
            
        combined[cid] = combined.get(cid, 0.0) + boost

    # Hard temporal filtering only when explicit temporal constraints exist.
    if has_temporal:
        filtered: dict[int, float] = {}
        for cid, score in combined.items():
            row = chunk_meta.get(cid)
            if not row:
                continue
            dt = extract_chunk_date(row["content"], row["section"], row["mtime"])
            if within_temporal_window(dt, temporal):
                filtered[cid] = score
        combined = filtered

    # 8) Diversify and Top-K
    ranked_ids = sorted(combined, key=combined.__getitem__, reverse=True)
    # Diversify results: avoid top-k being dominated by one file while still
    # allowing multiple high-signal sections from a strong match.
    top_ids: list[int] = []
    file_counts: dict[str, int] = {}
    max_per_file = 2
    for cid in ranked_ids:
        row = chunk_meta.get(cid)
        if not row:
            continue
        fp = row["file_path"]
        if file_counts.get(fp, 0) >= max_per_file:
            continue
        file_counts[fp] = file_counts.get(fp, 0) + 1
        top_ids.append(cid)
        if len(top_ids) >= top_k:
            break
    if not top_ids:
        return []

    # 9) Format results
    results = []
    for chunk_id in top_ids:
        row = chunk_meta.get(chunk_id)
        if not row:
            continue

        src = []
        if chunk_id in bm25_ranks:
            src.append("bm25")
        if chunk_id in vec_ranks:
            src.append("vector")
        if chunk_id in keyword_ranks:
            src.append("keyword")
        if chunk_id in graph_ranks:
            src.append("graph")
        if chunk_id in temporal_ranks:
            src.append("temporal")

        dt = extract_chunk_date(row["content"], row["section"], row["mtime"])
        results.append(
            {
                "file": row["file_path"],
                "section": row["section"],
                "excerpt": row["content"][:350].replace("\n", " ").strip(),
                "date": dt.strftime("%Y-%m-%d"),
                "score": round(combined[chunk_id], 4),
                "sources": "+".join(src) if src else "none",
            }
        )

    return results


def format_results(results: list[dict]) -> str:
    """Format search results for display in model context."""
    if not results:
        return "No results found."

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"[{i}] {r['file']} § {r['section']}  ({r['sources']}, score {r['score']}, date {r['date']})"
        )
        lines.append(f"    {r['excerpt']}")
        lines.append("")

    return "\n".join(lines).rstrip()

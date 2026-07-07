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
import yaml

from indexer import AIKB_ROOT, DB_PATH, embed

# ── Helpers ────────────────────────────────────────────────────────────────────

def recency_boost(mtime: float) -> float:
    """
    Return a score boost in [0, 0.016] that decays linearly over 14 days.

    Calibration: RRF contributions are ~1/(60+rank), so a #1 rank in one
    ranking list is worth ~0.0164. The boost is capped at one top vote so
    recency acts as a tiebreaker between comparably relevant chunks instead
    of letting any recently-touched file outrank canonical docs outright.
    """
    age_days = (time.time() - mtime) / 86400
    if age_days >= 14:
        return 0.0
    return round(0.016 * (1.0 - age_days / 14), 5)


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


def load_suppressions() -> list[dict]:
    path = AIKB_ROOT / "_runtime" / "suppressions.yaml"
    if not path.exists():
        return []
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(loaded, list):
        return []
    return [item for item in loaded if isinstance(item, dict)]


def is_suppressed(row: dict, suppressions: list[dict]) -> bool:
    file_path = row["file_path"]
    section = row["section"]
    for item in suppressions:
        if item.get("file") != file_path:
            continue
        suppressed_section = (item.get("section") or "").strip()
        if not suppressed_section or suppressed_section == section:
            return True
    return False


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


def entity_name_matches(name: str, query_tokens: set[str], normalized_query: str) -> float:
    """Return match strength in [0, 1]: 1.0 for exact name match, else the
    fraction of the name's segments covered by query tokens ("cross-agent-
    mind-meld" fully covered beats "gemini-cli" matching only "cli")."""
    if name in query_tokens or name == normalized_query:
        return 1.0
    segments = {segment for segment in re.split(r"[-_.]", name) if segment}
    if not segments:
        return 0.0
    return len(query_tokens & segments) / len(segments)


# Precise identifier kinds carry full weight; frontmatter tags a bit less.
# All kinds except host/tag are then discounted by link degree — an entity
# attached to 80 chunks localizes poorly no matter how precise its kind.
# (Hosts/tags are naturally high-degree: they answer broad queries.)
_ENTITY_KIND_WEIGHTS = {
    "host": 1.5, "file": 1.2, "path": 1.2, "alias": 1.0,
    "ip": 1.0, "tag": 0.8, "term": 1.0, "term-llm": 1.0, "port": 0.5,
}

# Chunks whose total match evidence stays below this never enter the entity
# ranking — keeps the channel sparse so weak generic-term matches don't earn
# a full RRF vote.
_ENTITY_SCORE_FLOOR = 0.5


def _entity_match_weight(kind: str, degree: int) -> float:
    base = _ENTITY_KIND_WEIGHTS.get(kind, 0.8)
    if kind in ("host", "tag"):
        return base
    if degree <= 25:
        return base
    if degree <= 80:
        return base * 0.4
    return base * 0.15


def build_entity_ranks(
    entity_rows: list[tuple[int, str, str, int]],
    query_tokens: set[str],
    normalized_query: str,
    chunk_ids: set[int],
    chunk_meta: dict[int, dict],
) -> dict[int, int]:
    if not entity_rows or not query_tokens:
        return {}

    chunk_entities: dict[int, dict[str, float]] = {}
    for chunk_id, name, kind, degree in entity_rows:
        if chunk_id not in chunk_ids:
            continue
        name = (name or "").lower()
        strength = entity_name_matches(name, query_tokens, normalized_query)
        if strength <= 0:
            continue
        weight = _entity_match_weight(kind or "term", degree or 1) * strength
        weights = chunk_entities.setdefault(chunk_id, {})
        weights[name] = max(weights.get(name, 0.0), weight)

    if not chunk_entities:
        return {}

    scored = []
    for chunk_id, weights in chunk_entities.items():
        meta = chunk_meta.get(chunk_id, {})
        tags = meta.get("tags", "").lower()
        host_matches = sum(1 for name in weights if name in query_tokens and f"host:{name}" in tags)
        score = sum(weights.values()) + (2 * host_matches)
        if score < _ENTITY_SCORE_FLOOR:
            continue
        text = f"{meta.get('section', '')} {meta.get('content', '')}".lower()
        text_hits = sum(1 for tok in query_tokens if re.search(rf"\b{re.escape(tok)}\b", text))
        scored.append((chunk_id, score, max(len(name) for name in weights), text_hits))

    scored.sort(key=lambda item: (item[1], item[2], item[3]), reverse=True)
    return {chunk_id: rank + 1 for rank, (chunk_id, _, _, _) in enumerate(scored[:60])}


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
    domain: str | None = None,
    project: str | None = None,
    kind: str | None = None,
    use_usage_stats: bool = True,
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
    coverage_ranks: dict[int, int] = {}
    try:
        safe_q = fts_safe(normalized_query)
        rows = conn.execute(
            "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT 60",
            (safe_q,),
        ).fetchall()
        bm25_ranks = {row[0]: i + 1 for i, row in enumerate(rows)}

        # Term-coverage list: chunks containing ALL meaningful query terms.
        # OR-based BM25 lets a chunk repeating one term many times outrank
        # the chunk that actually covers the whole query; this counterbalances.
        and_q = safe_q.replace(" OR ", " AND ")
        if " AND " in and_q:
            rows = conn.execute(
                "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT 60",
                (and_q,),
            ).fetchall()
            coverage_ranks = {row[0]: i + 1 for i, row in enumerate(rows)}
    except sqlite3.OperationalError:
        pass

    # 2) Load all chunk metadata + embeddings once.
    rows = conn.execute(
        "SELECT id, file_path, section, content, tags, mtime, embedding FROM chunks"
    ).fetchall()
    try:
        entity_rows = conn.execute(
            """SELECT ec.chunk_id, e.name, e.kind, d.cnt
               FROM entity_chunks ec
               JOIN entities e ON e.id = ec.entity_id
               JOIN (SELECT entity_id, COUNT(*) AS cnt
                     FROM entity_chunks GROUP BY entity_id) d
                 ON d.entity_id = e.id"""
        ).fetchall()
    except sqlite3.OperationalError:
        entity_rows = []
    # Usage signals keyed on (file_path, section); missing tables (pre-migration
    # DB) degrade to no boost/penalty.
    access_stats: dict[tuple[str, str], tuple[float, str]] = {}
    feedback_stats: dict[tuple[str, str], tuple[int, int, int, int]] = {}
    if use_usage_stats:
        try:
            access_stats = {
                (r[0], r[1]): (r[2], r[3] or "")
                for r in conn.execute(
                    "SELECT file_path, section, rank_weighted, last_retrieved FROM access_stats"
                ).fetchall()
            }
            feedback_stats = {
                (r[0], r[1]): (r[2], r[3], r[4], r[5])
                for r in conn.execute(
                    "SELECT file_path, section, stale, wrong, incomplete, duplicate FROM feedback_stats"
                ).fetchall()
            }
        except sqlite3.OperationalError:
            pass
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

    suppressions = load_suppressions()
    if suppressions:
        chunk_meta = {
            cid: meta
            for cid, meta in chunk_meta.items()
            if not is_suppressed(meta, suppressions)
        }
        if not chunk_meta:
            return []
        surviving_ids = set(chunk_meta.keys())
        bm25_ranks = {cid: r for cid, r in bm25_ranks.items() if cid in surviving_ids}
        coverage_ranks = {cid: r for cid, r in coverage_ranks.items() if cid in surviving_ids}

    # Apply filters: domain, project, kind
    if domain or project or kind:
        valid_kinds = {"doc", "event", "script", "state", "candidate"}
        if kind and kind not in valid_kinds:
            raise ValueError(f"Invalid kind '{kind}'. Must be one of {sorted(valid_kinds)}")

        norm_domain = domain.lower().rstrip("/") + "/" if domain else None
        proj_lower = project.lower() if project else None

        filtered_meta = {}
        for cid, meta in chunk_meta.items():
            fp = meta["file_path"]
            fp_lower = fp.lower()

            if norm_domain and not fp_lower.startswith(norm_domain):
                continue

            if proj_lower:
                tags_lower = meta["tags"].lower()
                if proj_lower not in fp_lower and proj_lower not in tags_lower:
                    continue

            if kind:
                actual_kind = "doc"
                if fp.startswith("_runtime/events/"):
                    actual_kind = "event"
                elif fp.startswith("_tools/") and meta["section"] == "script":
                    actual_kind = "script"
                elif fp == "_state.yaml":
                    actual_kind = "state"
                elif fp.startswith("_runtime/candidates/"):
                    actual_kind = "candidate"

                if actual_kind != kind:
                    continue

            filtered_meta[cid] = meta

        chunk_meta = filtered_meta
        if not chunk_meta:
            return []

        # Drop filtered-out ids from BM25 and coverage lists
        surviving_ids = set(chunk_meta.keys())
        bm25_ranks = {cid: r for cid, r in bm25_ranks.items() if cid in surviving_ids}
        coverage_ranks = {cid: r for cid, r in coverage_ranks.items() if cid in surviving_ids}

    # 3) Vector cosine similarity
    ids = list(chunk_meta.keys())
    embs = np.array([np.frombuffer(chunk_meta[cid]["embedding"], dtype=np.float32) for cid in ids])

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
    is_blocker_intent = bool(q_words & {"blocker", "blockers", "pending", "todo", "open"})
    is_eval_intent = bool(q_words & {"eval", "evaluation", "benchmark", "benchmarks", "harness"})
    q_slug = re.sub(r"[^a-z0-9]+", "-", normalized_query.lower()).strip("-")
    for cid, row in chunk_meta.items():
        fp = row["file_path"].lower()
        basename = fp.rsplit("/", 1)[-1]
        section = row["section"].lower()
        tags = (row["tags"] or "").lower()

        s = 0.0
        for tok in q_tokens:
            if tok in fp:
                s += 2.0
            if tok in basename:
                s += 2.0  # filename matches are stronger signal than directory
            if tok in section:
                s += 1.5
            if tok in tags:
                s += 1.0
        if q_slug and q_slug in fp:
            s += 3.0

        if s > 0:
            keyword_scores[cid] = s

        # Intent-aware priors to reduce false positives in broad corpora.
        # Calibrated to ~half a top RRF vote (1/61 ≈ 0.0164) so a prior can
        # break ties but never substitute for actual retrieval signal.
        p = 0.0
        if is_script_intent and fp.startswith("_tools/"):
            p += 0.008
        if is_eval_intent and fp.startswith("_tools/") and "eval" in basename:
            p += 0.008
        if is_agent_intent and fp.startswith("_agents/"):
            p += 0.008
        if is_memory_intent and fp.startswith("_tools/memory-"):
            p += 0.006
        if is_blocker_intent and (fp == "_state.yaml" or any(word in section for word in ("pending", "todo", "blocker"))):
            p += 0.006
            if "pending" in section:
                p += 0.005
        if p:
            prior_scores[cid] = p

    keyword_ranked = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:60]
    keyword_ranks = {cid: i + 1 for i, (cid, _) in enumerate(keyword_ranked)}
    entity_ranks = build_entity_ranks(
        entity_rows,
        q_tokens,
        normalized_query.lower(),
        set(chunk_meta.keys()),
        chunk_meta,
    )

    rankings: list[dict[int, int]] = [bm25_ranks, vec_ranks, keyword_ranks]
    if coverage_ranks:
        rankings.append(coverage_ranks)
    if entity_ranks:
        rankings.append(entity_ranks)

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

    # 7b) Usage signals (both bounded so they reorder near-ties, never
    # substitute for retrieval signal — the caps are the invariant).
    usage_boosted: set[int] = set()
    if access_stats or feedback_stats:
        now_ts = datetime.now().timestamp()
        for cid in list(combined.keys()):
            row = chunk_meta.get(cid)
            if not row:
                continue
            key = (row["file_path"], row["section"])

            # Access boost: up to half a top RRF vote (0.008), fading over 30
            # days since last retrieval. Mem0-style "memory decay", additive.
            stat = access_stats.get(key)
            if stat:
                rank_weighted, last_retrieved = stat
                freshness = 0.0
                try:
                    last_dt = datetime.fromisoformat(last_retrieved.replace("Z", "+00:00"))
                    age_days = (now_ts - last_dt.timestamp()) / 86400
                    freshness = max(0.0, 1.0 - age_days / 30)
                except (ValueError, AttributeError):
                    pass
                access = min(0.008, 0.004 * np.log1p(rank_weighted)) * freshness
                if access > 0:
                    combined[cid] += access
                    usage_boosted.add(cid)

            # Feedback penalty: capped at ~1.25 top votes (0.020) — demotes,
            # never buries. File-level feedback (section='') at half weight.
            # Duplicate is penalty-only: the flagged copy drops below its twin
            # without needing to identify the twin.
            penalty = 0.0
            fb = feedback_stats.get(key)
            if fb:
                stale, wrong, incomplete, duplicate = fb
                penalty += (0.010 * min(wrong, 2) + 0.008 * min(stale, 2)
                            + 0.004 * min(duplicate, 2) + 0.002 * min(incomplete, 2))
            fb_file = feedback_stats.get((row["file_path"], ""))
            if fb_file and row["section"] != "":
                stale, wrong, incomplete, duplicate = fb_file
                penalty += 0.5 * (0.010 * min(wrong, 2) + 0.008 * min(stale, 2)
                                  + 0.004 * min(duplicate, 2) + 0.002 * min(incomplete, 2))
            if penalty > 0:
                combined[cid] -= min(0.020, penalty)

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
        if chunk_id in entity_ranks:
            src.append("entity")
        if chunk_id in usage_boosted:
            src.append("access")

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

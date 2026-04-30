---
context: personal
tags: [aikb, memory, retrieval, scoring, ranking, conflicts, jarvis]
status: planning
last_updated: 2026-03-12
---

# AIKB Memory Retrieval + Scoring Spec
**Last Updated:** 2026-03-12
**Summary:** Phase 2 implementation spec for ranked memory retrieval, candidate prioritization, and conflict detection on top of AIKB runtime memory, including OpenViking-inspired retrieval ergonomics to roadmap.

---

## Goal

Close the remaining gap with memory-native platforms by enabling:
- fast ranked recall (`memory_search`)
- quality-aware prioritization for promotion work
- explicit conflict detection for contradictory memories

This layer sits above runtime capture/promotions and below response generation.

## OpenViking-Informed Retrieval Additions

The OpenViking comparison surfaced four retrieval features worth explicitly adding to AIKB's roadmap:
- stable resource addressing beyond raw file paths
- explicit abstract/overview/detail loading tiers
- more visible staged retrieval flow instead of opaque ranking
- a more coherent public retrieval interface across CLI/service/tooling

## Scope (Phase 2)

- In-scope:
  - Query-time ranked retrieval across runtime + canonical memory
  - Scoring model with transparent weights
  - Conflict records for contradictory memory items
- Out-of-scope:
  - Fully automatic canonical patch application
  - Vector DB dependency (initial version is dependency-light)

## Retrieval Surfaces

1. `runtime events` (`_runtime/events/*.ndjson`)
2. `memory candidates` (`_runtime/candidates/*.yaml`)
3. `canonical docs` (`*.md` excluding `_runtime/`, `_tools/`, `.git/`)

## `memory_search` API Contract (CLI v1)

```bash
python3 _tools/memory-pipeline/memory_search.py \
  --query "what did we decide about promotion policy" \
  --scope all \
  --limit 8
```

Arguments:
- `--query` (required): natural language query
- `--scope` (optional): `all|runtime|events|candidates|canonical`
- `--limit` (optional): top N (default `10`)
- `--include-rejected` (optional): include rejected candidates
- `--json` (optional): JSON output for tool chaining

Output fields:
- `id`
- `source` (`event|candidate|canonical`)
- `path`
- `uri` (when resource addressing is available)
- `status`
- `date`
- `score`
- `excerpt`

## Scoring Model (v1)

Total score:

`score = term_match + status_boost + recency_boost + confidence_boost + source_boost`

### Components
- `term_match`:
  - sum of query token match counts in normalized text
- `status_boost`:
  - `merged +2.0`
  - `approved +1.5`
  - `queued +0.5`
  - `rejected -1.0` (unless `--include-rejected`)
- `recency_boost`:
  - `max(0, 2.0 - age_days/14)`
- `confidence_boost`:
  - candidates only: `confidence` (0..1)
- `source_boost`:
  - canonical `+0.7`
  - event `+0.4`
  - candidate `+0.5`

## Planned Retrieval Stages (v2)

Move from a mostly monolithic score computation toward explicit stages:

1. **Addressing**:
   resolve query scope into files, chunks, and eventually stable AIKB resource URIs
2. **Cheap recall**:
   lexical recall plus optional L0 abstract matching
3. **Navigation recall**:
   L1 overview / section summary expansion for directories or large files
4. **Deep recall**:
   chunk-level lexical or semantic recall against canonical and runtime detail
5. **Rerank**:
   mix relevance, freshness, confidence, canonicality, and graph/temporal signals
6. **Trace emission**:
   record why top results survived each stage

## Retrieval Trace Contract (planned)

Each search should be able to emit an optional trace object for debugging and eval:

```yaml
trace:
  query: "what did we decide about promotion policy"
  stages:
    - stage: recall_lexical
      kept: 24
      dropped: 120
    - stage: overview_expand
      kept: 12
      notes: "expanded 3 high-value directories/files"
    - stage: rerank
      kept: 8
  top_result_reasons:
    - id: personal-projects/aikb-implementation-roadmap.md#phase-2-write-safety-and-governance
      reasons: ["canonical source", "high term match", "recently updated"]
```

## Conflict Detection Rules (v1)

A conflict candidate is raised when items share topic tokens but differ on mutually exclusive state markers:
- status words (`active` vs `decommissioned`, `pending` vs `complete`)
- action polarity (`enabled` vs `disabled`, `allow` vs `deny`)
- temporal contradiction (`as of` older claim vs newer claim)

Conflicts are written to `_runtime/conflicts/YYYY-MM-DD.yaml` and remain non-canonical until resolved.

## Data Contracts

Schemas:
- `_runtime/schemas/runtime-event.schema.json`
- `_runtime/schemas/memory-candidate.schema.json`
- `_runtime/schemas/memory-record.schema.json`
- `_runtime/schemas/memory-conflict.schema.json`

## Rollout Plan

### Week 1
- Implement `memory_search.py` with scoring + filters
- Validate top-10 quality on known queries
- Add repeatable benchmark runner: `_tools/memory-pipeline/eval_memory_search.py`

### Week 2
- Add conflict detector scaffold and output file format
- Integrate recall-first step into agent instructions

### Week 3+
- Add optional embeddings backend for semantic recall
- Add eval harness (`precision@k` on saved query sets)
- Add abstract/overview-aware staged loading for large files and directories
- Add search trace output for debugging and benchmark review

## Success Criteria

- >80% of known decision-recall queries return correct memory in top 3
- Retrieval latency <1s on current AIKB size for top 10
- Candidate review queue sorted by impact/relevance, not insertion order

## Immediate Next Actions

- [x] Create retrieval/scoring specification document
- [x] Add schema files for retrieval records and conflicts
- [x] Implement `memory_search.py` CLI (keyword + weighted ranking)
- [x] Add `conflict_scan.py` to generate conflict candidates
- [x] Add `resolve_conflicts.py` to manage conflict lifecycle states
- [x] Add evaluation query set and saved benchmark reports
- [x] Add repeatable `memory_search.py` benchmark harness
- [x] Extend benchmark harness with latency and at-risk query reporting
- [x] Add canonical markdown section chunking plus path-level deduping in retrieval results
- [ ] Expand eval set to cover runtime-event and candidate-heavy queries, not just canonical recall
- [ ] Tune ranking weights using at-risk query reports and reduce noisy file-type cross-talk
- [ ] Add a stable URI field to indexed retrieval records once the resource model lands
- [ ] Prototype L0/L1 generated summaries for high-value roadmap/runbook files and compare retrieval quality
- [ ] Add optional search trace output to `memory_search.py` and benchmark reports

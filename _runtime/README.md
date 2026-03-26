# Runtime Memory Staging

**Last Updated:** 2026-03-25
**Summary:** Non-canonical staging area for runtime capture, candidate generation, nightly dream consolidation, promotion review, scratchpads, graph data, and maintenance artifacts.

---

## Purpose

`_runtime/` captures high-signal session events before they are promoted into canonical AIKB documents.

- Canonical truth stays in domain/project files.
- `_runtime/` is a buffer and review zone.
- Nothing here is considered durable truth until promoted.

## Layout

- `events/` — append-only NDJSON event logs by date (`YYYY-MM-DD.ndjson`)
- `candidates/` — daily candidate bundles for review (`YYYY-MM-DD.yaml`)
- `promotion-queue.md` — manual queue for approve/reject/merge tracking
- `dreams/` — nightly dream-cycle outputs (`dream-summary`, `dream-facts`, `dream-procedures`, `dream-preferences`, `dream-rejections`)
- `dreams/dream-distilled-YYYY-MM-DD.md` — human-readable nightly synthesis built from the strongest dream bundles
- `dreams/dream-bundles-YYYY-MM-DD.json` — grouped clusters of related nightly dream memories
- `dreams/dream-quality-YYYY-MM-DD.json` — quality metrics for a nightly dream pass (ratios, bundle count, contradiction count, canonical signal)
- `schemas/` — JSON schema references for runtime memory data contracts
- `conflicts/` — daily conflict candidates detected across memory surfaces
- `conflicts/dream-YYYY-MM-DD.json` — contradiction snapshots detected during the nightly dream cycle
- `scratchpads/` — agent-editable per-session RAM blocks for temporary notes
- `graphs/` — temporal knowledge graph outputs from markdown links + runtime events
- `events/compacted/` — compacted historical event summaries
- `events/archive/` — optional gzip archives of old raw NDJSON event logs
- `maintenance/` — nightly maintenance logs

## Retention Policy (v1)

- Keep runtime event files for 30 days.
- Keep candidate files for 90 days.
- Keep dream artifacts for 30 days unless promoted into canonical docs or used for training datasets.
- Keep `promotion-queue.md` indefinitely (audit trail).

## Sensitivity & Security Rules

- Never store secrets in runtime logs.
- If an event includes sensitive material, replace with references:
  - `[Stored in Vaultwarden: <Item Name>]`
- Tag sensitive-but-useful entries as `restricted`.
- `restricted` items must never be auto-promoted.

## Event Schema (v1)

Required fields:
- `id`
- `ts_utc`
- `session_id`
- `agent`
- `type` (`decision|blocker|change|observation`)
- `project`
- `summary`
- `sensitivity` (`normal|restricted`)
- `promote_hint` (`candidate|ignore`)

Optional fields:
- `evidence` (array)

## Candidate Schema (v1)

- `id`
- `source_events`
- `target_file`
- `proposed_change`
- `confidence`
- `class` (`auto-promote-safe|needs-review|never-promote`)
- `status` (`queued|approved|rejected|merged`)

## Starter Commands

```bash
# Append one runtime event
python3 _tools/memory-pipeline/ingest_runtime.py \
  --agent codex \
  --session-id codex-demo-001 \
  --type decision \
  --project personal-projects/project-jarvis.md \
  --summary "Established runtime-memory staging architecture for AIKB." \
  --evidence "file:_runtime/README.md"

# Build candidate file for today and refresh queue
python3 _tools/memory-pipeline/build_candidates.py

# Review one candidate decision (syncs candidate YAML + queue row)
python3 _tools/memory-pipeline/review_candidates.py \
  --id cand_20260304_001 \
  --status merged \
  --reviewer tim \
  --notes "Merged into canonical file."

# Create markdown patch proposals from queued candidates
python3 _tools/memory-pipeline/propose_patches.py

# Build/query temporal knowledge graph
python3 _tools/memory-pipeline/build_temporal_graph.py
python3 _tools/memory-pipeline/query_temporal_graph.py --node truenas --after 2026-01-01

# Compact older event logs
python3 _tools/memory-pipeline/compact_events.py --older-than-days 21 --archive-raw
```

## Daily Management Checklist

1. Capture events during meaningful work phases.
2. Run `build_candidates.py` before session handoff/end.
3. Set each candidate to `merged` or `rejected` using `review_candidates.py`.
4. Ensure no stale `queued` items remain without reviewer notes.
5. Promote approved facts into canonical AIKB files and update `_state.yaml`.
6. Run `conflict_scan.py` and review/resolve high-confidence contradictions.

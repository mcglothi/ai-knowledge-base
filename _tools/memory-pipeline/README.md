# Memory Pipeline CLI

**Last Updated:** 2026-03-07
**Summary:** Runtime memory tooling for candidate generation, autonomous reorg, temporal graphing, retrieval evaluation, metadata validation, chunk-aware write previews, scratchpads, and nightly maintenance.

## Core Commands

```bash
python3 _tools/memory-pipeline/ingest_runtime.py --agent codex --session-id demo --type decision --project personal-projects/project-jarvis.md --summary "example"
python3 _tools/memory-pipeline/build_candidates.py --date 2026-03-06
python3 _tools/memory-pipeline/review_candidates.py --id cand_20260306_001 --status approved --reviewer tim --notes "validated"
python3 _tools/memory-pipeline/memory_search.py --query "promotion policy" --as-of 2026-03-01 --limit 8
python3 _tools/memory-pipeline/eval_memory_search.py --k 5
python3 _tools/memory-pipeline/validate_memory_metadata.py
python3 _tools/memory-pipeline/write_gateway.py --path personal-projects/project-jarvis.md --chunk-id personal-projects/project-jarvis.md#project-jarvis --mode append-to-section --text "## Example" 
python3 _tools/memory-pipeline/conflict_scan.py --scope all
```

## New Intelligence Features

```bash
# Autonomous memory reorg suggestions + queue sync
python3 _tools/memory-pipeline/autonomous_reorg.py --min-similarity 0.65 --stale-days 180
python3 _tools/memory-pipeline/queue_reorg_suggestions.py

# Virtual RAM blocks (scratchpads)
python3 _tools/memory-pipeline/scratchpad.py --action create --session-id codex-abc --title "Mid-session notes"
python3 _tools/memory-pipeline/scratchpad.py --action append --session-id codex-abc --text "Need to recheck DNS path"
python3 _tools/memory-pipeline/scratchpad.py --action close --session-id codex-abc

# Temporal knowledge graph
python3 _tools/memory-pipeline/build_temporal_graph.py
python3 _tools/memory-pipeline/query_temporal_graph.py --node truenas --after 2026-01-01 --limit 10

# Context compaction for older event logs
python3 _tools/memory-pipeline/compact_events.py --older-than-days 21
python3 _tools/memory-pipeline/compact_events.py --older-than-days 21 --archive-raw

# Nightly dream-cycle consolidation
python3 _tools/memory-pipeline/dream_cycle.py --date 2026-03-21

# Nightly orchestrator (runs candidates, dream cycle, reorg, queue sync, graph build, compaction)
python3 _tools/memory-pipeline/nightly_maintenance.py
```

## Scheduler Hook (macOS launchd)

```bash
bash _tools/memory-pipeline/install_nightly_launchd.sh
# Manual trigger after install:
launchctl start com.timmcg.aikb-nightly-maintenance
```

## Cron Hook (Linux/macOS)

```bash
bash _tools/memory-pipeline/install_nightly_cron.sh
# override schedule if needed:
SCHEDULE_HOUR=3 SCHEDULE_MINUTE=10 bash _tools/memory-pipeline/install_nightly_cron.sh
```

## Shutdown Hook (Linux systemd)

```bash
bash _tools/memory-pipeline/install_shutdown_service.sh
systemctl status aikb-shutdown-finalize.service --no-pager
```

- If the shutdown finalizer exits immediately under systemd, check whether `HOME` is set in the service environment.
- A prior failure mode came from launching the hook under `set -u` without `HOME`, which caused shell expansion to abort before any useful work ran.
- `install_shutdown_service.sh` now writes `Environment=HOME=...`, and `shutdown_finalize.sh` also falls back to `/home/mcglothi` when `HOME` is missing.

## Notes

- `build_candidates.py` now includes automated user preference fact extraction unless `--no-fact-extraction` is passed.
- `dream_cycle.py` emits non-canonical nightly memory artifacts in `_runtime/dreams/`, including a markdown summary plus JSONL files for facts, procedures, preferences, and rejected/noisy items.
- `dream_cycle.py` can ingest live Memory Core proposals by status, fall back to local proposal fixtures when the API is unavailable, and writes contradiction snapshots to `_runtime/conflicts/dream-YYYY-MM-DD.json`.
- `dream_cycle.py` now applies a lightweight canonical signal score so durable project/home-lab docs outrank repo-maintenance churn when summarizing recent canonical git changes.
- `dream_cycle.py` now uses target-file hints, proposal kinds, and imperative/procedure phrasing to better separate `fact`, `procedure`, and `preference` memories.
- `dream_cycle.py` now emits `dream-bundles-YYYY-MM-DD.json` and `dream-quality-YYYY-MM-DD.json` so the nightly pass can cluster related memories and score the quality of each dream run in a portable, public-template-friendly format.
- `dream_cycle.py` now emits `dream-distilled-YYYY-MM-DD.md`, a human-readable synthesis of what the system learned, what procedures to keep, what preferences to preserve, and what noise it rejected.
- `memory_search.py` supports hybrid keyword+semantic ranking, explicit date windows (`--as-of`, `--before`, `--after`), and indexes Markdown, YAML, Python, and shell files outside `_runtime/`.
- `eval_memory_search.py` benchmarks `memory_search.py` against `_runtime/benchmarks/search-eval-set.json` and writes a dated markdown report.
- `validate_memory_metadata.py` checks title/header/frontmatter consistency and can run in warning-only or strict-frontmatter mode.
- `write_gateway.py` previews or applies chunk-aware markdown edits using `path` + `chunk_id`, updates `Last Updated`, and keeps writes inside the AIKB root.
- `autonomous_reorg.py` output is queued into `_runtime/promotion-queue.md` through `queue_reorg_suggestions.py`.
- `compact_events.py --archive-raw` compresses older `events/*.ndjson` into `events/archive/*.ndjson.gz` and writes summaries to `events/compacted/*.json`.

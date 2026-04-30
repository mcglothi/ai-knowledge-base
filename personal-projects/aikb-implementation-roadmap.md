---
tags: [aikb, memory, roadmap, implementation, retrieval, graph, memory-core, governance]
status: planning
last_updated: 2026-04-13
---

# AIKB Implementation Roadmap
**Last Updated:** 2026-04-13
**Summary:** Consolidated implementation backlog derived from the March 2026 AIKB benchmarks. Turns the identified gaps into a phased to-do list with dependencies, ownership surfaces, and success checks, including the 2026-03-12 OpenViking comparison takeaways, the 2026-04-08 public-template packaging priorities, and the 2026-04-10 public-template sync/adoption review.

---

## Goal

Move AIKB from "strong canonical memory substrate" toward a practical self-hosted memory platform with:
- stronger retrieval quality and latency
- safer multi-agent writes
- better structured metadata
- graph and temporal reasoning sidecars
- clearer lifecycle management across repo memory, runtime staging, and Memory Core

## Working Principles

1. Markdown + Git remain the canonical source of truth.
2. Retrieval can move into read-optimized sidecars.
3. Mutation should be Git-backed and diff-oriented, not opaque API-owned state.
4. Runtime memory stays reviewable and policy-governed before canonical merge.
5. Every phase should improve operator usefulness, not just architectural elegance.

## Delta From OpenViking Review (2026-03-12)

The OpenViking comparison confirmed that AIKB is ahead on governed canonical memory, but behind on productized context abstractions and retrieval ergonomics. The roadmap additions below intentionally borrow the strongest OpenViking ideas without giving up AIKB's core principles.

Priority themes to absorb:
- first-class resource/URI model across canonical docs, runtime artifacts, skills, and external resources
- explicit L0/L1/L2 context surfaces instead of relying mostly on handcrafted headers
- retrieval observability with traceable selection paths
- cleaner public API/CLI surfaces for memory navigation and search
- packaging AIKB Memory Core and related tooling as a reusable installable product

## Public Template Packaging Priorities (2026-04-08)

The next public-template wave should emphasize features that are easy to explain, immediately valuable in week one, and visibly different from generic "AI memory in markdown" setups.

### Roll in now

- Operator intents as a first-class public feature.
  - Why: this is the clearest "teach once, reuse forever" workflow in the system.
  - Packaging bar: template file, starter runbook, README/docs mention, and examples that map shorthand requests to explicit execution plus verification.

### Roll in next

- Runtime HUD + closeout workflow as the operator-facing daily loop.
  - Why: this makes AIKB feel active instead of archival and gives users a concrete habit around session hygiene.
  - Packaging bar: one-command starter flow, screenshots or terminal snippets, and conservative defaults.
  - Progress 2026-04-08: public template docs now include `docs/operator-loop.md`, README operator-loop onboarding, and a smaller "first useful habit stack" path in getting-started. Public repo head after this packaging pass: `170c234`.
  - Progress 2026-04-08 (later): public template now also includes `_tools/feature-tour.sh`, a guided terminal walkthrough that teaches the operator loop, approvals, operator intents, and search as an adoption sequence instead of a scattered feature list.

- Pending approvals as a trust surface.
  - Why: community users will trust the system more if high-impact actions are visible and reviewable.
  - Packaging bar: simple examples, clear "when to use this" guidance, and no requirement to adopt the full memory pipeline.
  - Progress 2026-04-08: added example approval rows and clearer usage framing in the public template `_pending_approvals.md`.

- Semantic search as the first "wow" addon after base install.
  - Why: it gives immediate payoff without requiring users to understand every file layout detail.
  - Packaging bar: fast setup, plain-language examples, and stronger guidance around when search beats manual file loading.
  - Progress 2026-04-08: public `docs/search-setup.md` now includes starter queries and explicit guidance on when to search versus read files directly.

### Media packaging note

- Screenshot and GIF creation should be treated as a separate automation surface.
  - Screenshot generation is the easier first step and should be automated before animation.
  - GIF generation is feasible, but likely needs an explicit dependency choice (`ffmpeg`, `gifski`, or a browser-recording path) so the workflow stays reproducible across machines.

### Coordination hardening note

- Active-session coordination now needs repo and scope awareness, not just a freeform task label.
  - 2026-04-08 direction: extend `_agents/active.md` to claim `Repo` + `Scope`, and add a `runtime_cli.py check-repo --path ...` helper so unexpected dirty repos trigger a coordination/crash-recovery check instead of silent guesswork.
  - 2026-04-08 follow-through: add `runtime_cli.py claim-session` and `release-session` so agents can register scoped claims mechanically instead of hand-editing markdown rows.

### Template update channel note

- 2026-04-10 review: the public template was on the right track, but the update channel needed one more hardening pass before "periodic sync checks" could become a default recommendation.
  - Fixed in public repo commit `b46879d`: `install.sh` now personalizes the repo-root `AGENTS.md` in addition to `_agents/*.md`, so Codex sessions opened inside the user's AIKB repo inherit their own repo/path/secrets defaults instead of Tim-specific ones.
  - Fixed in public repo commit `b46879d`: `sync.sh` now tracks `last_checked_utc`, `last_seen_upstream_sha`, and `last_applied_upstream_sha` in `.aikb-config.d/template-sync-state.json`, and `./sync.sh --check` compares upstream changes against the last applied upstream SHA instead of against personalized working-tree files.
  - Fixed in public repo commit `b46879d`: added `sync-agents.sh` so Codex project repos can be bulk re-synced after template instruction changes.
  - Follow-up direction: add a slightly richer agent-facing nudge policy around stale `last_checked_utc` so tools can suggest `./sync.sh --check` after the TTL expires without auto-applying tracked framework updates.
  - Implemented in public repo commit `7c7f581`: added `runtime_cli.py template-sync` with `--auto-check` and `--force-check`, so agents have one safe helper that reads `.aikb-config.d/template-sync-state.json` and only runs `./sync.sh --check` when the saved check window is stale or when forced by the operator.
  - Implemented in public repo commit `7c7f581`: the runtime HUD and prompt now surface template freshness as `current`, `stale`, or `pending`, which gives agents and operators a lightweight reminder channel without auto-applying tracked framework updates.
  - Implemented in public repo commit `75ac82e`: `runtime_cli.py template-sync` now supports `--set-interval <days>`, so the operator can keep the default weekly cadence or temporarily tighten it during active template rollout periods.
  - Implemented in public repo commit `75ac82e`: when a template update is pending, the helper now prints a reusable operator-facing message that explicitly reassures the user that framework updates do not touch personal data or canonical custom content.
  - Next likely step: decide whether the default session-start loop for Claude/Gemini/Codex should proactively call `runtime_cli.py template-sync --auto-check`, or whether that helper should stay as an operator-loop convention first.

### Independent Review Takeaways (2026-04-13)

A recent independent review of the AIKB "disposable session context" model confirmed that treating AIKB as the durable buffer is the correct move, but identified "context amputation" during compaction as the primary risk.

#### Roll in next

- **Working Memory Snapshot Tier**
  - Why: Compaction currently saves "Decisions" but loses "Momentum" (live edge, next 3 steps, rejected paths, transient invariants).
  - Implementation: A tiny, structured `session_state.md` or `session_state.json` artifact that is updated before every `/compact` and loaded during `wake-up`.

- **Native Token Observability**
  - Why: The "Token Economy" is currently policy-driven, not data-driven. We need to prove the savings.
  - Implementation: Add token-delta telemetry to `_runtime/gemini-invocations.ndjson` to track `tokens_saved` per capture+compact cycle.

- **Contextual Recall Hardening**
  - Why: Frictionless retrieval is the only thing preventing agents from relapsing into expensive full-file reading.
  - Implementation: Harden the Graph-RAG and Intent-Aware scoring implemented on 2026-04-13 to ensure near-zero friction for "re-finding the live edge" after a fresh wake-up.

## Master To-Do List

### Phase 0: Foundation and Guardrails

- [x] **Graph-RAG & Intent-Aware Search** — 2026-04-13. Implemented relationship expansion and intent-weighted priors in `aikb-search`.
- [x] **Memory Event Indexing** — 2026-04-13. `indexer.py` now scans `_runtime/events/` directly.
- [ ] **Working Memory Snapshot Tier** (Formalize handover artifact for compaction).
- [ ] **Token Economy Observability** (Telemetry for compaction savings).
- [ ] Define a strict metadata contract for canonical docs, runtime candidates, proposals, and graph entities.
  - Deliverables: schema fields for `type`, `scope`, `confidence`, `freshness`, `provenance`, `merge_policy`, `entity_refs`.
  - Depends on: none
  - Success metric: all newly created memory objects validate against the contract.

- [ ] **Priority: Auto-Capture & Ingestion Paths**
  - [ ] Build an **MCP `remember()` tool** for agent-initiated explicit writes (agent-driven).
  - [x] **Claude Code `Stop` hook** (`aikb-session-stop.sh`) — 2026-04-12. Auto-captures closeout event, runs build_candidates, releases active.md claim, auto-commits _runtime/. Wired into ~/.claude/settings.json.
  - [ ] Formalize the **Hybrid Ingestion Strategy**: all agents write to append-only NDJSON logs (`_runtime/events/`) to prevent Git race conditions during concurrent sessions.

- [ ] Standardize frontmatter and header expectations across AIKB memory-producing files.
  - Deliverables: one reference spec plus validation script.
  - Depends on: metadata contract
  - Success metric: lint run reports zero missing required fields on targeted files.

- [ ] Add stable chunk IDs and target spans for indexed canonical content.
  - Deliverables: chunk ID format, indexer changes, stored span references.
  - Depends on: metadata contract
  - Success metric: search results can point to stable chunk IDs instead of only file paths.

- [ ] Expand the benchmark harness to track latency, false positives, and category drift in addition to hit-rate.
  - Deliverables: updated eval dataset, timing capture, error tagging.
  - Depends on: none
  - Success metric: weekly benchmark reports quality plus performance regressions.

- [ ] Define an AIKB URI/resource model that maps canonical docs, runtime artifacts, skills, and external resources into one navigable namespace.
  - Deliverables: URI scheme, resource taxonomy, path-mapping rules, and read-only compatibility layer over the current repo structure.
  - Depends on: metadata contract
  - Success metric: retrieval and tooling can address memory objects by stable URI as well as filesystem path.

### Phase 1: Retrieval and Search Serving

- [ ] **YAML Tag-based Selective Loading**
  - Deliverables: standard `tags: []` frontmatter and instructions for agents to use tags for context pruning instead of full-file loads.
  - Success metric: agents successfully identify and load only relevant sub-sections of large directories without vector search.

- [ ] Generate explicit L0/L1/L2 context artifacts or cached summaries for high-value AIKB directories and files.
  - Deliverables: abstract/overview generation flow, storage format, invalidation rules, and benchmark comparison against header-only navigation.
  - Depends on: metadata contract, stable chunk IDs
  - Success metric: agents can do cheap relevance checks and directory navigation without opening full files.

- [ ] Refactor `memory_search` to use a clear retrieval pipeline: lexical recall, optional semantic recall, rerank, merge.
  - Deliverables: retrieval-stage abstraction inside the CLI/service.
  - Depends on: stable chunk IDs
  - Success metric: search internals support swapping backends without changing caller UX.

- [ ] Add a local vector read-replica while keeping Markdown as source of truth.
  - Deliverables: index build job, storage choice, sync job from canonical files and runtime artifacts.
  - Depends on: stable chunk IDs, metadata contract
  - Success metric: improved precision and lower latency on the benchmark set.

- [ ] Add metadata-aware filtering to retrieval.
  - Deliverables: filters for project, source type, time window, status, confidence, freshness.
  - Depends on: metadata contract, vector or structured index
  - Success metric: scoped queries return cleaner top-5 results.

- [ ] Add reranking for mixed lexical/semantic results.
  - Deliverables: pluggable rerank step and evaluation comparison.
  - Depends on: retrieval pipeline refactor
  - Success metric: MRR improves without hurting latency beyond target budget.

- [ ] Add retrieval trace output and observability views.
  - Deliverables: trace payload showing recall, filters, rerank decisions, and final chunk/file selection; optional operator-facing report or UI view.
  - Depends on: retrieval pipeline refactor, stable chunk IDs
  - Success metric: at-risk or surprising results can be debugged without reading code or raw logs.

- [ ] Improve benchmark coverage for runtime-heavy and candidate-heavy queries.
  - Deliverables: larger eval set with segmented categories and failure annotations.
  - Depends on: none
  - Success metric: benchmark set reflects real operator tasks, not only canonical recall.

- [ ] Reduce ranking noise on currently at-risk queries surfaced by the eval harness.
  - Deliverables: ranking adjustments for buried results, benchmark-artifact suppression, and file-type cross-talk reduction.
  - Depends on: expanded benchmark harness
  - Success metric: risky query count drops materially while hit-rate stays stable.

### Phase 2: Write Safety and Governance

- [ ] Build a Git-backed write gateway for AIKB mutations.
  - Deliverables: API or CLI surface that prepares diffs, validates targets, updates `Last Updated`, and writes via controlled patches.
  - Depends on: metadata contract
  - Success metric: normal agent workflows stop handling raw Git conflict resolution directly.
  - Progress: `write_gateway.py` exists and `proposals_cli.py apply` now routes through it in preview-first mode, with local normalization/inference for missing `suggested_file`, `suggested_chunk_id`, and `apply_mode`.

- [x] **`aikb_review` Reconciliation Command**
  - Deliverables: A human-in-the-loop script that reconciles the event log into canonical docs via a "Review/Approve" diff flow.
  - Success metric: stale or conflicting facts are identified and resolved before canonical merge.
  - Progress 2026-04-12: `_tools/memory-pipeline/aikb_review.py` now provides interactive queued-candidate triage with approve/reject/skip, source-event drill-down, and `review_candidates.py` integration.

- [ ] Make proposal application document-aware instead of line-fragile.
  - Deliverables: section targeting, chunk targeting, diff preview, rejection reasons.
  - Depends on: stable chunk IDs, write gateway
  - Success metric: approved proposals can be applied safely with previewable diffs.

- [ ] Replace batch-only promotion handling with an event-driven local queue or daemon.
  - Deliverables: queue processor for runtime events, candidate generation, and proposal updates.
  - Depends on: write gateway
  - Success metric: candidate freshness no longer depends mainly on cron cadence.

- [ ] Formalize promotion classes and auto-apply policy.
  - Deliverables: `auto-promote-safe`, `needs-review`, `never-promote`, plus rule examples.
  - Depends on: metadata contract, write gateway
  - Success metric: low-risk updates can be auto-applied without format regressions.

- [ ] Add review-capacity metrics and backlog hygiene rules to Memory Core.
  - Deliverables: queue age, proposal aging, auto-expiry or archive rules.
  - Depends on: queue lifecycle work
  - Success metric: proposal backlog remains bounded and observable.

- [ ] Keep the URI/resource layer read-first by default and require explicit proposal/write policies for canonical mutation.
  - Deliverables: permission model for `read`, `propose-write`, `apply-write`, and policy mapping to Memory Core / local tooling.
  - Depends on: AIKB URI/resource model, write gateway
  - Success metric: AIKB gains product-like resource ergonomics without weakening governance boundaries.

### Phase 3: Graph and Temporal Intelligence

- [ ] Extract entities and relations into a sidecar graph index.
  - Deliverables: entity schema, relation types, extractor from canonical docs and runtime artifacts.
  - Depends on: metadata contract, stable chunk IDs
  - Success metric: graph queries answer relationship questions better than token-overlap expansion.

- [ ] Upgrade temporal graphing from artifact generation to retrieval-serving primitive.
  - Deliverables: time-aware edges, state transitions, query interface by `before/after/as-of`.
  - Depends on: graph index, metadata contract
  - Success metric: time-bounded queries return materially better answers than today.

- [ ] Add contradiction and stale-fact detection across canonical memory and runtime memory.
  - Deliverables: freshness rules, contradiction reports, review workflow.
  - Depends on: metadata contract, graph or retrieval sidecars
  - Success metric: stale operational facts are surfaced automatically for review.

- [ ] Connect graph signals back into `memory_search` and proposal ranking.
  - Deliverables: graph-aware recall or rerank features.
  - Depends on: graph index, retrieval pipeline
  - Success metric: multi-hop and dependency queries improve on the benchmark set.

### Phase 4: Lifecycle Unification and Operator UX

- [ ] Define a single lifecycle model for `observed -> candidate -> proposal -> canonical -> stale -> archived`.
  - Deliverables: shared status vocabulary across runtime files, Memory Core, and tooling.
  - Depends on: metadata contract, queue work, write gateway
  - Success metric: every memory artifact has a clear state and transition rule.

- [ ] Align local AIKB runtime files and AIKB Memory Core proposals under the same lifecycle schema.
  - Deliverables: schema mapping, sync rules, drift checks.
  - Depends on: lifecycle model
  - Success metric: no split-brain ambiguity between repo state and Memory Core state.

- [ ] Add operator-facing dashboards for retrieval quality, queue health, and memory drift.
  - Deliverables: dashboard views or reports for search metrics, proposal backlog, stale facts.
  - Depends on: benchmark expansion, queue metrics
  - Success metric: operator can see memory system health at a glance.

- [ ] Publish a cleaner AIKB memory API/CLI surface for navigation, retrieval, proposal review, and lifecycle inspection.
  - Deliverables: consolidated command surface and/or service endpoints that wrap current internal scripts behind stable interfaces.
  - Depends on: URI/resource model, retrieval pipeline refactor, lifecycle model
  - Success metric: common memory tasks no longer require knowing individual internal script names.

- [ ] Add "always visible" working-memory blocks for active projects and active sessions.
  - Deliverables: explicit project/session memory surfaces with tight size and lifecycle controls.
  - Depends on: lifecycle model
  - Success metric: agents need fewer repeated repo lookups for recurring session state.

- [ ] Package AIKB Memory Core and core memory tooling as a reproducible install/deploy product.
  - Deliverables: install docs, compose/deploy paths, versioned packaging, and a minimal "bring up AIKB memory stack" workflow for new environments.
  - Depends on: API/CLI surface, lifecycle model
  - Success metric: a new machine or homelab target can stand up the AIKB memory runtime without bespoke session knowledge.

## Immediate Execution Order

1. ✅ **Claude Code Stop hook** (`aikb-session-stop.sh`) — done 2026-04-12
2. ✅ **`wake-up` command** (`runtime_cli.py wake-up`) — done 2026-04-12
3. ✅ **Slim agent instructions** (`claude-code.md` rev9, 132 lines) — done 2026-04-12
4. **MCP `remember()` tool**: Basic agent-driven ingestion. [Codex task filed]
5. ✅ **`aikb_review` interactive CLI**: Candidate review loop. Done 2026-04-12.
6. ✅ **Vector search**: `memory_search.py --mode keyword|semantic|hybrid` plus local SQLite embedding index with keyword fallback. Done 2026-04-12.
7. **Slim remaining agent files** (codex.md, gemini.md, etc.) [Gemini task filed]
8. Metadata contract and frontmatter validation.
9. AIKB URI/resource model.
10. Stable chunk IDs and expanded benchmark harness.
11. Git-backed write gateway.
12. Retrieval pipeline refactor plus vector read-replica.
13. L0/L1/L2 context artifacts and retrieval tracing.
14. Metadata-aware filtering, reranking, and **Tag-based loading**.
15. Event-driven candidate/proposal queue.
16. Sidecar graph extraction and temporal query support.
17. Lifecycle unification across repo + Memory Core.
18. Public API/CLI consolidation and packaging.

## Suggested Workstreams

### Workstream A: Retrieval
- `memory_search.py`
- `eval_memory_search.py`
- canonical indexers
- vector read-replica

### Workstream B: Governance / Writes
- proposal application flow
- write gateway
- promotion policies
- review backlog controls

### Workstream C: Graph / Temporal
- `build_temporal_graph.py`
- graph extraction sidecar
- dependency and time-aware query support

### Workstream D: Memory Core
- proposal queue APIs
- runtime lifecycle alignment
- observability and queue hygiene

## Definition of Done

- Search remains benchmarked weekly with category and latency reporting.
- Agents mutate AIKB through a Git-backed validated path instead of ad hoc file writes.
- Retrieval can use lexical, vector, and graph signals without changing canonical storage.
- Temporal and contradiction-aware queries work on real operator tasks.
- Memory Core and local AIKB runtime staging use one lifecycle model and do not drift.

## Related Files

- `personal-projects/aikb-memory-runtime-upgrade.md`
- `personal-projects/aikb-memory-retrieval-scoring.md`
- `projects/aikb-knowledge-graph.md`
- `home-lab/services/aikb-memory-core.md`
- `_runtime/benchmarks/aikb-2026-03-07.md`
- `_runtime/benchmarks/openviking-2026-03-12.md`

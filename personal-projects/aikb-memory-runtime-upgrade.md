---
context: personal
tags: [aikb, memory, runtime-memory, ingestion, promotion-pipeline, governance, jarvis, dreaming]
status: planning
last_updated: 2026-04-12
---

# AIKB Runtime Memory Upgrade
**Last Updated:** 2026-04-12
**Summary:** Design proposal to close two key AIKB gaps: automatic context ingestion during sessions and governed promotion of validated knowledge into canonical AIKB files, now extended with a nightly "dream cycle" that consolidates runtime memory before any optional LoRA fine-tuning.

---

## Why This Upgrade Exists

Current AIKB is excellent as canonical memory, but it relies on manual updates. For Kyloch-scale continuity, AIKB needs:
- Automatic capture of high-signal session events
- A reviewable pipeline that promotes only validated facts into canonical docs

This preserves AIKB's strengths (auditability, git history, human control) while adding runtime memory benefits.

## OpenViking-Informed Additions

The 2026-03-12 OpenViking comparison highlighted a few runtime ideas worth adopting without weakening AIKB governance:
- a first-class resource model for runtime events, candidates, skills, and canonical targets
- explicit abstract/overview/detail layers for runtime memory objects
- more observable session compression and retrieval traces
- a cleaner operator-facing runtime API/CLI surface instead of mostly internal scripts

These are roadmap additions, not a rewrite away from git-native canonical memory.

## The Two Gaps (Explicit)

1. **Automatic context ingestion**
- Important session events are easy to lose if not manually written
- Agents need low-friction memory capture during work, not only at checkpoints

2. **Governed promotion to canonical memory**
- Not all runtime events should become durable truth
- We need a controlled "candidate -> verified -> merged" workflow

## Target State Architecture

### Layer 1: Runtime Capture (Ephemeral + Daily)
- Capture event records during active sessions:
  - decisions
  - blockers
  - commands/results summaries
  - file-change intent
- Store in an append-only runtime log outside canonical docs
- Keep events time-stamped and source-attributed (agent + session id)
- Assign stable resource IDs / URIs so downstream retrieval, review, and promotion can reference runtime objects without brittle file-path assumptions

### Layer 2: Candidate Memory Store (Review Queue)
- Aggregate and deduplicate captured events into candidate facts
- Attach confidence and evidence pointers (source event ids)
- Classify candidates:
  - `auto-promote-safe` (low-risk metadata)
  - `needs-review` (most operational facts)
  - `never-promote` (ephemeral/unsafe/noisy)
- Generate lightweight L0/L1 summaries for candidate groups so reviewers and agents can triage without always opening raw payloads

### Layer 3: Canonical Promotion (AIKB Files)
- Promotion creates explicit patch proposals against existing AIKB files
- Human approves high-impact edits before merge
- All accepted promotions update:
  - target file
  - `Last Updated`
  - `_index.md` (if status changed)
  - `_state.yaml` recent changes (if material)

## Minimal Data Model

```yaml
runtime_event:
  id: evt_20260304_001
  ts_utc: "2026-03-04T19:10:00Z"
  session_id: "codex-abc123"
  agent: "codex"
  type: "decision|blocker|change|observation"
  project: "personal-projects/project-kyloch.md"
  summary: "Router policy defaults to local model, API escalation on complexity."
  evidence:
    - "tool_output_ref:turn42"
  sensitivity: "normal|restricted"
  promote_hint: "candidate"
```

```yaml
memory_candidate:
  id: cand_20260304_014
  source_events: ["evt_20260304_001", "evt_20260304_007"]
  target_file: "personal-projects/project-kyloch.md"
  proposed_change: "Add model-routing policy subsection."
  confidence: 0.86
  class: "needs-review"
  status: "queued|approved|rejected|merged"
```

## Promotion Policy (v1)

### Auto-promote-safe
- Non-sensitive factual metadata with direct evidence:
  - date stamps
  - file relocations
  - status flips where source-of-truth is explicit

### Needs-review (default)
- Architecture decisions
- Operational procedures
- Anything affecting security, cost, or production behavior

### Never-promote
- Raw command noise
- speculative statements
- secrets/credentials
- temporary runtime state ("job running")

## Operational Workflow (Day-to-Day)

1. **Auto-Capture**: Agents write runtime events during work via:
   - **Claude Code `Stop` hook**: Automated extraction to `_runtime/events/` at session end.
   - **MCP `remember()` tool**: Explicit agent-driven writes during the session.
   - **Hybrid Event Log**: All agents append to NDJSON logs to avoid Git race conditions.
2. **Candidate Builder**: Runs periodically or at end-of-session to aggregate events.
3. **`aikb_review` (Reconciliation)**: Human-in-the-loop script to review, reconcile, and approve candidates.
4. **Canonical Promotion**: Approved candidates become AIKB patches merged into canonical docs.

## Nightly Dream Cycle

The new nightly layer should behave more like memory consolidation than model training.
Its job is to transform a noisy day of runtime capture into a cleaner, dated, reviewable memory package.

### Inputs

- recent runtime events from `_runtime/events/*.ndjson`
- Memory Core proposals by status (`new`, `approved`, `applied`, `rejected`)
- canonical AIKB diffs from the last 24 hours
- event compaction summaries from `_runtime/events/compacted/*.json`

### Outputs

- `dream-summary-YYYY-MM-DD.md`
- `dream-facts-YYYY-MM-DD.jsonl`
- `dream-procedures-YYYY-MM-DD.jsonl`
- `dream-preferences-YYYY-MM-DD.jsonl`
- `dream-rejections-YYYY-MM-DD.jsonl`

### Required transformations

- deduplicate repeated facts across sessions and machines
- normalize vague time references like "today" and "yesterday" into absolute dates
- collapse assistant chatter and prompt residue into operator-relevant facts or discard them
- mark contradictions for review instead of silently merging them
- preserve evidence pointers back to runtime event ids and proposal ids
- separate "trainable memory" from "retrieve-only memory"

### Why this belongs before LoRA

LoRA should not learn directly from raw runtime logs or noisy proposal output.
The dream cycle is the quality gate that turns episodic capture into a compact, safer training candidate set.

## Runtime UX / API Roadmap Additions

- [x] Add an initial unified runtime API/CLI front door for `capture` and `status`.
- [x] Add a compact `hud` view that surfaces active task, runtime memory source, verification state, and approvals for day-to-day operator use.
- [x] Add a lightweight `focus` workflow so the HUD can surface the current objective and next verification step during active work.
- [x] Add an opt-in shell-hook capture path for high-signal commands so runtime events can be harvested during normal terminal work with conservative promotion defaults.
- [x] Add an approvals CLI over `_pending_approvals.md` so operator sign-off can be created and resolved through commands while remaining Git-visible and HUD-visible.
- [ ] Expand the runtime API/CLI surface to `list`, `summarize`, `review`, and `promote`.
- [ ] Represent runtime objects with stable IDs/URIs that survive file movement and compaction.
- [ ] Generate abstract/overview/detail layers for candidate bundles and important session archives.
- [ ] Capture retrieval/promotion traces so a reviewer can answer "why did this proposal exist?" quickly.
- [ ] Preserve the current governance rule: runtime systems may propose canonical edits, but canonical writes stay preview-first and policy-gated.

## Proposed File Layout (inside AIKB)

```
AIKB/
├── _runtime/
│   ├── README.md
│   ├── events/
│   │   └── YYYY-MM-DD.ndjson
│   ├── candidates/
│   │   └── YYYY-MM-DD.yaml
│   └── promotion-queue.md
└── _tools/
    └── memory-pipeline/
        ├── ingest_runtime.py
        ├── build_candidates.py
        └── propose_patches.py
```

`_runtime/` is intentionally non-canonical. Canonical truth remains domain/project files.

## Guardrails

- No secrets in runtime or candidate logs (same Vaultwarden rule as AIKB)
- Sensitive events tagged and excluded from auto-promotion
- Immutable event ids; no silent mutation
- Promotion always produces a human-readable diff

## Success Metrics

- 80%+ reduction in "forgotten session context" incidents
- <5 minutes from session end to candidate queue ready
- >90% of merged promotions accepted without rework
- Zero secrets written to runtime or canonical memory

## Phase Plan

### Phase 1 (MVP, 1-2 weeks)
- Create `_runtime/` structure
- Implement event append + daily rollup
- Manual review queue in markdown (`promotion-queue.md`)

### Phase 2 (2-4 weeks)
- Candidate dedupe/scoring
- Patch proposal generator against target files
- Approval command flow (approve/reject with rationale)
- Ranked retrieval layer (`memory_search`) across runtime + canonical memory
- Retrieval/scoring spec reference: `personal-projects/aikb-memory-retrieval-scoring.md`

### Phase 3 (4-8 weeks)
- Policy tuning per domain (home-lab, personal-projects, side-gigs)
- Auto-promote-safe lane
- Dashboard for candidate backlog and merge stats

### Phase 4 (Nightly Dreaming)
- Add `dream_cycle.py` to the nightly orchestrator after candidate generation and before archival compaction
- Produce structured daily dream artifacts plus a short operator-facing markdown summary
- Introduce contradiction buckets and confidence downgrade rules for unresolved conflicts
- Track dream-cycle quality metrics: dedupe rate, contradiction count, promoted fact count, rejected noise count
- Keep the dream phase read-mostly with proposal-first writes into canonical AIKB

## Immediate Next Actions

- [x] Create `_runtime/README.md` with retention and sensitivity policy
- [x] Define `runtime_event` schema and validation rules
- [x] Build end-of-session candidate generation prototype
- [x] Pilot on `project-kyloch.md` and one home-lab file
- [x] Create retrieval/scoring specification and schema set
- [x] Scaffold `memory_search.py` ranked retrieval CLI
- [ ] **Implementation: Claude Code `Stop` hook + `aikb-ingest` extraction script.**
  - Progress: added a structured `runtime_cli.py closeout` / `aikb closeout` path so operator wrap-up phrases can emit a real session-closeout runtime event with repo, queue, and focus context before final shutdown reporting.
- [ ] **Implementation: MCP `remember()` tool for direct agent writes.**
- [x] **Implementation: `aikb_review` reconciliation CLI.**
  - Progress: added `_tools/memory-pipeline/aikb_review.py`, an interactive approve/reject loop over queued candidates with source-event inspection and optional `propose_patches.py` handoff.
- [ ] Measure false-positive promotions before enabling auto-promote-safe
- [x] Add an operator-facing `runtime_cli.py` for event capture plus a concise status summary of sessions, event bundles, and queue health
- [ ] Add stable runtime resource IDs/URI conventions to the event and candidate schemas
- [ ] Prototype abstract/overview generation for session archives or candidate bundles
- [ ] Define trace payloads for proposal evidence and promotion decisions
- [ ] Add stable IDs and status filters to the approvals CLI so HUD-linked approval flows are deterministic and scriptable
- [ ] Add richer HUD/prompt stats (usage counters, recency windows, source mix) sourced from runtime memory without overwhelming the operator
- [ ] Package prompt/hook presets so the console surface is easy to enable consistently across supported shells and machines
- [x] Add a nightly dream-cycle prototype that consumes runtime events, proposal states, and recent canonical diffs
- [ ] Define a trainability label (`trainable`, `retrieve_only`, `reject`) for dream outputs

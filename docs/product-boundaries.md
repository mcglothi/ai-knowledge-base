# AIKB Product Boundaries
**Status:** Draft for team review
**Last Updated:** 2026-05-01

## Purpose
This document defines what belongs in the public `ai-knowledge-base` product surface before broader public launch.

Primary goal: keep AIKB focused on its core differentiator:

> **Shared, persistent, inspectable memory that any AI tool can read and write — owned by the operator, not the platform.**

AIKB is strongest when it is clearly understood as a **cross-agent, cross-session, cross-machine memory layer**.

---

## What AIKB Is
AIKB is:
- a local-first, Git-backed memory substrate for AI tools
- a shared context layer across agents, sessions, and machines
- an operator-owned and human-auditable knowledge base
- a practical operating pattern for wake-up, handoff, and closeout
- a cross-agent system with explicit coordination primitives

---

## What AIKB Is Not
AIKB is not:
- a hosted SaaS memory platform
- a black-box memory API
- a full autonomous agent runtime
- a general-purpose homelab platform
- a benchmark lab as part of the core product story
- a dashboard-first product
- a grab bag of unrelated AI automation experiments

---

## Boundary Rule
A feature belongs in default AIKB core only if it is required to help multiple AI tools share durable, inspectable context across sessions and machines.

If a feature is useful but not required for that promise, it should usually be:
- advanced-but-core,
- an extension,
- a companion project,
- or experimental.

---

## Product Tiers

### 1. Core
Ships with the default product and should be part of the day-one story.

Core includes:
- Git-backed flat-file knowledge store
- schema and file conventions
- `_index.md` and `_state.yaml` conventions
- `runtime_cli.py`
- wake-up / orientation flow
- closeout / persistence flow
- search / retrieval
- `aikb-search` as the standard search layer
- runtime staging + promotion pipeline
- agent portability overlays/instructions
- **Agent IM**
- **Mind Meld**
- operator ownership and auditability

#### Why Agent IM and Mind Meld are core
AIKB's differentiation is not only persistent memory, but **cross-agent continuity**.

That requires:
- a **push channel** for explicit agent-to-agent coordination (`Agent IM`)
- a **shared awareness protocol** for avoiding duplicated work and understanding neighboring activity (`Mind Meld`)

Without these, AIKB risks collapsing into a single-user notes/memory system rather than a true cross-agent substrate.

#### Why `aikb-search` is core
Search is not just a convenience. It is how operators and agents verify that memory actually works across sessions.

Without a real search layer, “retrieval” becomes ad hoc grep and the product promise weakens. It does not need to be the very first step a user configures, but it should be part of the standard AIKB path.

---

### 2. Advanced-but-Core
Included in the main repo, but not required for first success.
These support mature use without defining the public product surface.

Examples:
- template sync workflow
- claim/release discipline
- token economy / compaction guidance
- richer maintenance and review helpers
- MCP setup docs
- architecture notes for deeper adopters
- agent handoff patterns
- self-maintenance helpers such as proposal/reorg support if kept near-core

Design rule:
- keep available
- do not lead with them in onboarding
- do not make a new user understand them before first value

---

### 3. Extensions
Optional capabilities that may be useful, but are not required for the core AIKB promise.

Likely extension candidates:
- dream cycle / nightly consolidation
- temporal graph build/query
- approvals HUD / operator control surfaces
- autonomous reorg / proposal machinery if separated from advanced-core
- richer platform-specific integrations
- platform adapters

Design rule:
- visible as optional
- documented separately
- not part of the first-run mental model

---

### 4. Companion Projects
Related projects or example stacks that may demonstrate AIKB or support specific environments, but should not define the main product.

Likely companion candidates:
- UI / HUD surfaces such as `aikb-bootstrap`
- richer web/demo surfaces
- environment-specific operational bundles

Design rule:
- clearly labeled
- physically separated enough that new users do not confuse them with the core product

#### Public template decision: `home-lab/`
`home-lab/` should move out of the public template surface.

Reason:
- it is highly personal
- it does not represent the generic AIKB product
- it confuses new users about whether AIKB is a memory platform or a homelab operating environment

---

### 5. Experimental
Useful for dogfooding or research, but not part of the stable public surface.

Examples:
- unfinished pipeline experiments
- ranking/scoring ideas
- benchmark artifacts that do not affect normal user flow
- early-stage automation concepts
- local inference/runtime experiments

Design rule:
- not in the onboarding path
- clearly labeled unstable or experimental

---

## Draft Classification for the Public Template

### Core
- `README.md`
- `AGENTS.md`
- `_agents/`
- `_runtime/`
- `_templates/`
- `_index.md`
- `_state.yaml`
- `install.py`, `install.sh`, `sync.sh`, `sync-agents.sh`
- `docs/getting-started.md`
- `docs/agent-im.md`
- `docs/mind-meld.md`
- `docs/operator-loop.md`
- `docs/search-setup.md`
- `docs/secrets-management.md`
- `docs/stop-hook-setup.md`
- `docs/windows-wsl.md`
- `_tools/memory-pipeline/runtime_cli.py`
- lifecycle and promotion pipeline tooling
- `_tools/aikb-search/`

### Advanced-but-Core
- `docs/token-economy.md`
- `docs/mcp-setup.md`
- `docs/hierarchical-aikb-design.md`
- review/maintenance helpers that support core behavior but are not day-one essentials
- handoff and self-maintenance patterns

### Extension Candidates
- `dream_cycle.py`
- `build_temporal_graph.py`
- `query_temporal_graph.py`
- `nightly_maintenance.py`
- `autonomous_reorg.py`
- `queue_reorg_suggestions.py`
- `proposals_cli.py` / `propose_patches.py` if separated from advanced-core
- `approvals_cli.py`

### Companion / Non-Core Surface
- `preview/`
- demo/branding assets not required for normal use
- UI/HUD surfaces such as `aikb-bootstrap`

### Experimental / Internal
- `sidecar.py`
- `eval_memory_search.py`
- benchmark or scoring harnesses

### Legacy / Deprecate Carefully
- `install_legacy.sh`

---

## Public Positioning Guidance
The public template should lead with:
1. shared memory
2. cross-agent continuity
3. cross-machine portability
4. Git-backed ownership and auditability
5. simple operator loop
6. real search/retrieval as part of the standard setup

It should not lead with:
- dream cycles
- graph features
- dashboards
- sidecars
- benchmarks
- homelab examples
- internal maintenance complexity

---

## Immediate Cleanup Priorities
Highest confusion-to-value items to move out of the default surface first:
1. dream cycle / temporal graph
2. approvals / dashboard / operator-heavy extras
3. homelab-specific content in the public-facing path
4. platform or environment-specific extras that are not required for first use
5. legacy setup surface

---

## Working Decisions
The following decisions are now treated as the working plan for Phase A:
- Agent IM is core
- Mind Meld is core
- `runtime_cli.py` is explicit core surface
- `aikb-search` is core, even if configured just after initial install
- `home-lab/` should move out of the public template surface
- `sidecar.py` is experimental, not extension
- `eval_memory_search.py` is experimental, not extension

---

## Proposed Next Step
After team review lock:
1. finalize classifications
2. label current files and docs by tier
3. rewrite README and getting-started around the core story
4. introduce migration-safe structure changes
5. validate on at least one non-owner install path

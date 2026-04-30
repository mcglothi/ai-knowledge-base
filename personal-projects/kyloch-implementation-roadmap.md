---
tags: [kyloch, jarvis-alias, roadmap, implementation, voice, hopper, turing, ai-hub, aikb, planning]
status: active
last_updated: 2026-04-12
---

# Kyloch Implementation Roadmap
**Last Updated:** 2026-04-12
**Summary:** Step-by-step implementation roadmap for building Kyloch as a runtime fabric, with milestone gates, dependencies, explicit defer decisions, a session-friendly action plan, and a running progress changelog.

---

## Naming Note
- **Canonical name:** Kyloch
- **Historical alias:** Project Jarvis / Jarvis

## Recent Progress

- **2026-04-12** — Consolidated five Kyloch planning docs into three. Merged `kyloch-runtime-fabric.md` + `kyloch-voice-architecture.md` into `kyloch-architecture.md`. Stripped changelog and business direction from `project-kyloch.md`. Removed doc redundancy that was creating orientation confusion across sessions.
- **2026-04-11** — Added design review to this roadmap. Identified five critical/architecture-level issues: JSON persistence risk, missing telemetry, missing auth before multi-device, undefined Hopper/Turing failure contract, ElevenLabs vs chatterbox identity lane decision. All five added to `_state.yaml` pending.
- **2026-04-11** — Added comprehensive Hopper-first voice-stack direction, chatterbox premium lane positioning, and multi-node hardware strategy to `project-kyloch.md`.
- **2026-04-11** — Built `kyloch-runtime-fabric.md` defining the system as a runtime fabric with tiered model fleet, task classes, routing policy, task packet schema, memory/tool/endpoint fabric, and control-plane responsibilities.
- **2026-04-11** — Built `kyloch-voice-architecture.md` with full API surface (Hopper voice gateway + Turing control plane), session schema, deployment shape, and build phases.
- **2026-04-11** — Added `personal-projects/kyloch-implementation-roadmap.md` as the execution-layer companion with milestone gates, dependencies, and step-by-step action plan.
- **2026-04-10** — Added operator-facing runtime memory CLI at `_tools/memory-pipeline/runtime_cli.py`; wired `aikb status`, `aikb hud`, `aikb focus`, and `aikb approvals` command surfaces.
- **2026-04-03** — Established the private GitHub repo `mcglothi/kyloch` with `docs/vision-and-direction.md`, `docs/architecture/overview.md`, `docs/endpoints/README.md`, and thin `apps/desktop-client/` Node CLI as the first endpoint path.
- **Earlier** — Split the first control-plane slice into `~/code/kyloch/apps/control-plane`. Initial endpoints: `/kyloch/contracts`, `/kyloch/sessions/register`, `/kyloch/route`, `/kyloch/briefing`, `/kyloch/approvals`, `/kyloch/devices`. Persistence is currently lightweight JSON — SQLite migration is the next critical step before any real client is wired.
- **Earlier** — Built `_tools/voice-router/` prototype on tesla: browser-based router that can send spoken or typed prompt to `codex`, `claude`, or `gemini` and read back response with browser TTS. Verified end-to-end with Codex and Gemini.

---

## Goal
Turn the Kyloch vision into a buildable system without painting the architecture into a corner.

This roadmap assumes:
- `hopper` is the front-of-house low-latency runtime node
- `turing` is the control-plane and AIKB-aware orchestration node
- Home Assistant is the endpoint/context fabric
- AIKB remains the canonical architecture, memory, and planning source of truth

## Guiding Rule
Build **stable seams before rich experiences**.

In practice that means:
- session and task contracts before pretty clients
- routing and control plane before many endpoints
- baseline voice runtime before premium voice polish
- one excellent desktop path before room hardware

## What Success Looks Like

### Near-term
- one desktop endpoint can talk to Hopper and get grounded answers through Turing
- sessions are tracked centrally
- routing between fast-path and deeper-path work is explicit
- approvals and AIKB status are accessible through the same runtime

### Mid-term
- phone shares the same session model
- watch supports short commands and approvals
- one room satellite works reliably

### Long-term
- Kyloch behaves like a multi-endpoint operating layer, not a collection of demos

## Explicit Non-Goals For Early Phases
- custom Echo-style room hardware
- TV-first experience
- multi-user identity and permissions
- split inference / KV-cache transport experiments
- mandatory premium TTS on the hot path
- deep proactive autonomy before approvals/governance are mature

## Phase Map

### Phase 0 — Contract Freeze
Objective:
- define the core system contracts that every later service and client will rely on

Why this phase matters:
- this is the phase that most directly prevents future corner-painting

Deliverables:
- session schema
- task packet schema
- task-class taxonomy
- endpoint identity model
- approval-level taxonomy
- model-role registry schema
- initial service boundaries for Hopper vs Turing

Exit criteria:
- future services can be designed against contracts instead of guesswork
- no endpoint is allowed to invent its own session semantics

Dependencies:
- `kyloch-runtime-fabric.md`
- `kyloch-voice-architecture.md`

### Phase 1 — Turing Control Plane MVP
Objective:
- stand up the canonical Kyloch brain-side services on Turing

Deliverables:
- session registry API
- routing API
- AIKB briefing/status API
- approvals API
- device registry API
- model registry API

Suggested home:
- define the Kyloch control plane as its own private service and add only the needed AI Hub integration points

Exit criteria:
- Hopper and future endpoints have one control plane to call
- AIKB and approvals are available without frontend-specific glue

Dependencies:
- Phase 0 contracts

### Phase 2 — Hopper Front-Door Runtime MVP
Objective:
- stand up the fast-path runtime on Hopper

Deliverables:
- voice gateway service
- Tier 0 interrupt/wake/control path
- STT adapter (`faster-whisper`)
- Tier 1 orchestrator lane
- baseline TTS adapter
- event stream back to Turing

Exit criteria:
- Hopper can accept a turn, route it, and return a spoken response
- Turing owns canonical session state while Hopper owns hot-path interaction

Dependencies:
- Phase 0 contracts
- Turing control-plane endpoints from Phase 1

### Phase 3 — Desktop Endpoint MVP
Objective:
- create the first user-facing endpoint against the real fabric

Deliverables:
- desktop push-to-talk client
- transcript / status panel
- streaming event handling
- reconnect/resume behavior

Preferred approach:
- evolve `_tools/voice-router/` into a real fabric-aware desktop client or reuse its proven parts

Exit criteria:
- daily-usable desktop flow
- desktop no longer behaves like a standalone toy app

Dependencies:
- Phase 1
- Phase 2

### Phase 4 — Specialist Routing
Objective:
- add real model specialization without destabilizing the core loop

Deliverables:
- first Tier 2 deep reasoning lane
- first Tier 2 coding lane
- retrieval lane wiring
- routing rules for escalation
- latency and fallback policy

Exit criteria:
- Tier 1 can escalate intentionally rather than over-answering
- model roles become visible and testable

Dependencies:
- stable desktop MVP
- baseline observability

### Phase 5 — Mobile Ingress
Objective:
- attach phone to the same runtime

Deliverables:
- phone endpoint or HA-integrated mobile path
- push-to-talk / hold-to-talk
- session continuation from desktop
- notifications and approval re-entry

Exit criteria:
- one session can move between desktop and phone

Dependencies:
- Phase 3

### Phase 6 — Watch Quick Command Surface
Objective:
- make the watch useful without overloading it

Deliverables:
- quick note capture
- short status queries
- stop/cancel path
- lightweight approvals

Exit criteria:
- watch can do 3-5 high-value things reliably

Dependencies:
- Phase 5 or an equivalent phone bridge

### Phase 7 — Room Satellite Pilot
Objective:
- prove one ambient endpoint only after the fabric is stable

Deliverables:
- one room satellite path
- wake-word handling
- audio playback
- home/status commands

Exit criteria:
- one room endpoint is reliable enough to leave deployed

Dependencies:
- mature Phase 2 runtime
- stable interruption behavior

## Milestone Gates

### Gate A — Architecture Safe
Required before service implementation expands:
- Phase 0 contracts written
- host responsibilities clear
- defer list accepted

### Gate B — Control Plane Safe
Required before endpoint proliferation:
- Turing APIs exist
- approvals and AIKB status are routable through one service layer

### Gate C — Runtime Safe
Required before premium voice or extra endpoints:
- Hopper hot path is stable
- interruption works
- baseline STT/TTS are good enough

### Gate D — Endpoint Safe
Required before room hardware:
- desktop flow is daily-usable
- phone is attached or clearly next

## Workstreams

### Workstream A — Contracts and Schemas
Artifacts:
- session schema
- task packet schema
- event schema
- approval-level schema
- model registry schema

Priority:
- highest

### Workstream B — AI Hub Control Plane
Artifacts:
- backend routes
- session persistence
- approval integration
- device and model registry surfaces

Priority:
- highest

### Workstream C — Hopper Runtime
Artifacts:
- voice gateway
- STT/TTS adapters
- router/orchestrator integration
- event forwarding

Priority:
- highest

### Workstream D — Endpoint UX
Artifacts:
- desktop client
- phone endpoint
- watch integration

Priority:
- medium after contracts and services exist

### Workstream E — Routing and Model Stewardship
Artifacts:
- first Tier 1 model choice
- first Tier 2 model choices
- routing policy rules
- model registry population

Priority:
- medium, but decisions should start early

### Workstream F — Observability and Reliability
Artifacts:
- latency logs
- failure buckets
- session trace views
- route-decision inspection

Priority:
- medium-high; do not postpone too long

## Immediate Step-By-Step Action Plan

### Step 1 — Write the core contracts
Create:
- Kyloch session schema
- task packet schema
- event taxonomy
- endpoint trust levels
- approval classes

Output:
- one contract doc or schema set in AIKB and/or repo

### Step 2 — Decide where the control-plane code lives
Decision:
- extend `ai-hub` backend vs create a dedicated Kyloch control-plane service

Default recommendation:
- start inside `ai-hub` to minimize early fragmentation

Output:
- architectural decision recorded in AIKB

### Step 3 — Define the first Turing APIs
Implement or specify:
- `POST /kyloch/sessions/register`
- `POST /kyloch/route`
- `GET /kyloch/briefing`
- `GET /kyloch/approvals`
- `GET /kyloch/devices`

Output:
- API contract doc and/or initial backend stubs

### Step 4 — Decide the first model-role assignments
Choose:
- Tier 1 orchestrator candidate
- first Tier 2 reasoning model
- first Tier 2 coding model
- STT lane
- baseline TTS lane
- premium TTS lane

Output:
- role table in AIKB

### Step 5 — Design the Hopper voice gateway around the contracts
Define:
- inbound audio flow
- text fallback flow
- event streaming format
- interrupt behavior
- Turing handoff rules

Output:
- service design doc and endpoint spec

### Step 6 — Re-scope the desktop client
Task:
- decide whether `_tools/voice-router/` is upgraded directly or used as a prototype to extract from

Output:
- decision + first implementation target

### Step 7 — Build the narrowest end-to-end slice
Slice:
- desktop push-to-talk
- Hopper STT
- Tier 1 route
- Turing AIKB briefing
- baseline spoken response

Output:
- first end-to-end runnable Kyloch flow

## First Build Slice Recommendation
If we start coding next, the first concrete slice should be:

1. Turing session + route + briefing APIs
2. Hopper voice gateway with text input and audio input support
3. desktop client using the new contracts
4. one AIKB-backed question flow
5. one approval/status flow

This is the smallest slice that proves the fabric instead of just proving speech-to-text.

### Current implementation status
- `~/code/kyloch/apps/control-plane` now holds the first persisted Kyloch control-plane seam.
- Initial endpoints exist for contracts, session registration, route decisions, briefings, approvals, and devices.
- The current persistence layer is intentionally lightweight (`apps/operator-console/data/jarvis-control-plane.json`) so the payloads can settle before committing to a larger service split or database schema.
- Companion implementation note: `~/code/kyloch/docs/kyloch-control-plane.md`

## Repo / Service Decisions

### Decided
- **`mcglothi/kyloch` (private)** — canonical home for Kyloch control-plane, identity, session fabric, routing, approvals, and device registry. `apps/control-plane` is the first implementation slice.
- **`mcglothi/ai-hub`** — operator-console UI surface. Integrates with the Kyloch control-plane via API; is not the canonical home of private runtime logic.
- **Hopper voice runtime** — lives either as a new service in `ai-hub` (if audio/runtime stays lightweight) or as a sibling service/repo (if it grows substantially). Decide after the control-plane is deployed.

### Delay deciding
- room-device firmware repo
- separate watch app repo

Those can wait until the contracts and runtime stabilize.

## Model Role Table To Finalize

| Role | Tier | Host | Initial Direction | Status |
|------|------|------|-------------------|--------|
| Realtime control | 0 | Hopper | deterministic services | define |
| Voice orchestrator | 1 | Hopper | small fast local model | choose |
| Baseline conversational lane | 1/2 | Hopper | local generalist | choose |
| Deep reasoning specialist | 2 | Turing or Hopper | local reasoning model | choose |
| Coding specialist | 2 | Turing or Hopper | local coding model | choose |
| Retrieval embedder | 2 | Turing | embedding model/service | choose |
| Retrieval reranker | 2 | Turing | reranker model/service | choose |
| STT | speech | Hopper | `faster-whisper` | chosen direction |
| Baseline TTS | speech | Hopper | low-latency local TTS | choose |
| Premium TTS | speech | Hopper/Turing | `chatterbox` | chosen direction |

## Risks To Watch
- designing the desktop client before the session/task contracts
- letting Hopper accumulate control-plane logic
- overcommitting to a TTS engine before latency is measured
- letting model experimentation outrun routing policy
- building watch/room flows before the desktop path is solid

---

## Design Review — 2026-04-11

Independent design review of Kyloch direction. Items ordered by urgency.

### Critical — Do before first real client is wired

**1. Replace JSON persistence with SQLite**
`apps/control-plane/data/kyloch-control-plane.json` has no concurrent write safety, no queryability, and no history. Sessions and approvals under real load will either corrupt state or require a custom read-modify-write wrapper. Switch to SQLite before attaching any real client — it is a small change now and a painful refactor later. Even `better-sqlite3` with a 5-table schema covers everything the current JSON does and survives restarts cleanly.

**2. Wire per-turn telemetry from the first working flow**
The runtime fabric doc correctly lists observability metrics (STT latency, route decision time, TTS start, end-to-end turn time) but places them at "medium-high, don't postpone." In voice systems you cannot improve what you don't measure. Append-to-JSONL is sufficient at first. Without this, optimization decisions will be driven by anecdote.

**3. Add auth to the control plane before multi-device**
The current control plane has no auth. One-operator LAN use from a desktop is fine without it, but the moment the phone or watch talks to Turing you need it. JWT with a shared secret or device-scoped API keys is sufficient for v1. Retrofitting auth is always messier than adding it early.

### Architecture — Define before services are wired together

**4. Write the Hopper/Turing failure contract**
The architecture says Turing owns canonical session state while Hopper owns the hot path, but the failure modes are unspecified. What happens when Turing is unreachable — does Hopper degrade to local-only mode, queue requests, or fail hard? Define this contract (even a single decision doc) before wiring them together, not after it surfaces at runtime.

**5. Decide voice identity lane: ElevenLabs vs. chatterbox**
`DAIDENTITY.md` references a stored ElevenLabs voice as the canonical Kyloch voice. The architecture positions `chatterbox` as the premium local lane. These imply different privacy postures, cost models, and latency profiles. This is an identity decision that must be resolved before the voice identity layer is built — otherwise it gets built twice. ElevenLabs = cloud + cost + privacy exposure. Chatterbox = local + clonable + unproven at streaming latency under interruption. Pick one as the identity lane, the other as fallback/experiment.

**6. Treat Home Assistant as integration, not structural dependency**
HA is a pragmatic choice for room satellites and presence signals, but using it as a structural dependency for phone/watch ingress adds real operational overhead — HA versioning, Wyoming protocol quirks, companion app behavior. Keep HA as a first-class integration but ensure the phone and watch paths work without it even if HA enriches them.

### Design hygiene — Worth addressing as the system matures

**7. Prevent routing-logic hardening before real Tier 1 model exists**
If `/kyloch/route` accumulates special-case classification logic before a real local model is on the Tier 1 slot, the result is a hand-rolled intent parser that becomes entrenched. Get a model candidate on Tier 1 before the routing code solidifies.

**8. Keep `preferred_execution_lane` in task packets abstract**
The vision includes eventual KV-cache / split-inference across nodes. The defer list is right to push this out, but ensure the task packet schema stays abstract enough that cross-node routing can be added later without redesigning packet semantics.

**9. Separate the business direction from the personal assistant architecture**
`project-kyloch.md` blends the personal operating layer vision with a commercial AI-agency direction (lead intake departments, productized services, etc.). These have different system requirements, trust models, and SLAs. If the business direction becomes serious, it deserves its own doc. Mixing them creates ambiguity about which requirements drive design decisions.

**10. Consolidate planning doc changelog / status surface**
Four AIKB Kyloch docs now exist plus repo docs. The `Recent Progress` section in `project-kyloch.md` is doing double duty as a running changelog and will drift. Recommended: keep AIKB docs architectural/canonical, move active implementation status to `_state.yaml` pending items, and use a single changelog file in the repo for session-by-session progress.

## Resume-Next-Session Checklist
When picking this back up in a future session:

1. Read:
   - `personal-projects/project-kyloch.md` — vision orientation (2 min read)
   - `personal-projects/kyloch-architecture.md` — system design, API surface, session model
   - `personal-projects/kyloch-implementation-roadmap.md` — this file; check Recent Progress and pending items
2. Confirm the Kyloch private repo (`mcglothi/kyloch`) remains the canonical home for control-plane work.
3. Read `~/code/kyloch/docs/kyloch-control-plane.md` and inspect `apps/control-plane/server.js`.
4. Check `_state.yaml` pending items for Kyloch — SQLite migration, telemetry, auth, failure contract, and voice identity decision are all flagged.
5. Wire one real client/runtime path against the contracts before adding more surfaces.

## Recommended Next Session Focus
The next highest-leverage session should do exactly one thing:

**Wire one end-to-end client path against the contracts.**

That means:
- register a desktop or Hopper session through `/kyloch/sessions/register`
- use `/kyloch/route` for a real request handoff
- replace stub briefing content with AIKB-backed briefing assembly
- prove one approval/status round-trip using stable IDs

Once that loop works, the rest of the runtime can expand with much less guesswork.

## Linked Docs
- [`project-kyloch.md`](project-kyloch.md) — vision and direction
- [`kyloch-architecture.md`](kyloch-architecture.md) — system design, API surface, session model, deployment shape
- [`newton-model-strategy.md`](newton-model-strategy.md) — model portfolio and lane-selection guidance

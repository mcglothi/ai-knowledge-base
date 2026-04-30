---
tags: [kyloch, jarvis-alias, architecture, runtime-fabric, voice, hopper, turing, home-assistant, ai-hub, aikb, orchestration, agents, stt, tts, session, api]
status: active
last_updated: 2026-04-16
---

# Kyloch Architecture
**Last Updated:** 2026-04-16
**Summary:** System-level architecture for Kyloch as a runtime fabric — covering host roles, tiered model fleet, task routing, memory layers, voice components, API surface, session model, deployment shape, and design traps. Merges the former kyloch-runtime-fabric.md and kyloch-voice-architecture.md.

---

## Naming Note
- **Canonical name:** Kyloch
- **Historical alias:** Project Jarvis / Jarvis

---

## Core Decision
Do **not** build Kyloch as:
- one frontend with one "main assistant model"
- one voice app with bolted-on tools
- one giant general-purpose model that tries to do everything

Build Kyloch as a **runtime fabric**:
- a shared control plane
- a routed model fleet
- a memory layer
- a tool/action layer
- a multi-endpoint session fabric

The voice assistant is one surface of the runtime fabric, not the architecture itself.

---

## Host Role Split

### Hopper — front-of-house runtime node (`10.10.10.200`)
- low-latency voice ingress
- wake word / VAD / interrupt path
- STT
- fast router/orchestrator model
- baseline conversational lane
- baseline TTS
- short-lived voice turn state

Optimize for: responsiveness, always-on posture, lightweight task completion, first decision point.

### Turing — control plane and memory node (`10.10.10.50`)
- canonical session registry
- AI Hub / operator-console
- AIKB retrieval and summarization
- approval queue/state
- tool gateway
- device registry
- policy engine
- async orchestration coordination

Optimize for: consistency, visibility, control, cross-endpoint continuity.

### Home Assistant — endpoint and context fabric (`babbage`)
- notifications
- presence/context signals
- mobile/watch/room/TV integration
- Assist/Wyoming-compatible device pathways
- low-risk home-control actions

Treat Home Assistant as a first-class integration, **not** a structural dependency. Phone and watch paths must work without it even if HA enriches them.

---

## Tiered Runtime Model

### Tier 0 — Realtime non-LLM control
- wake word, VAD, interruption, mute/stop/cancel
- audio session state, endpoint audio transport
- deterministic where possible
- no dependency on the main LLM path
- local-first

### Tier 1 — Fast orchestrator / front-door model
- owns the first reasoning pass for nearly every request
- intent classification
- session-aware dialogue steering
- decides local answer vs specialist vs tool call vs approval
- normalizes requests into task packets
- shapes tool arguments
- keeps lightweight conversation fluid

Desired traits: small, cheap, fast, robust at structured outputs. This is the real "Kyloch conversational brain" for the hot path — not the deepest reasoning model.

### Tier 2 — Specialist model lanes
- performs higher-value or domain-specific work when Tier 1 decides escalation is warranted
- deep reasoning / synthesis
- coding / repo work
- research / long-form drafting
- retrieval / reranking
- premium TTS
- future multimodal vision/document lanes

Tier 2 should not sit on the hot path by default.

### Tier 3 — Async worker and background agents
- long summarization
- repo scans
- nightly memory consolidation
- recommendation generation
- monitoring follow-ups
- proactive briefings

### Tier 4 — Optional cloud escalation
- explicit policy, bounded by data-sensitivity and cost rules
- never assumed as the default path

---

## Task Classes

| Class | Examples | Owner |
|-------|----------|-------|
| A — Realtime control | stop, mute, cancel, wake/acknowledge | Tier 0 only |
| B — Fast conversational | status checks, simple questions, short summaries, home-control queries | Tier 1 ± light tool calls |
| C — Memory-grounded | AIKB lookups, "what changed today?", "status of X?", pending approvals | Tier 1 → Turing memory/tool fabric |
| D — Specialist synchronous | deeper reasoning, architecture synthesis, code understanding, multi-step ops | Tier 1 escalates to Tier 2 |
| E — Deferred/async | background scans, longer reports, overnight tasks, proactive briefings | Tier 3 |

---

## Routing Policy
Every turn should answer in order:
1. Can this be handled in Tier 0?
2. Can Tier 1 answer well enough on its own?
3. Does this require memory/tool grounding from Turing?
4. Does this require a Tier 2 specialist?
5. Should this become an async task instead of a blocking answer?
6. Does it require approval?
7. Is cloud escalation allowed or necessary?

**Preferred policy order:** deterministic local controls first → cheap local routing → local memory/tool grounding → specialist local models → async decomposition → cloud only last.

---

## Task Packet Schema
Kyloch normalizes work into task packets to prevent frontend-driven spaghetti.

```yaml
task_id: string
session_id: string
origin_device_id: string
task_class: A|B|C|D|E
requested_mode: desk|mobile|watch|room|car
user_text: string
normalized_intent: string
context_refs: [string]         # AIKB paths or session memory refs
required_tools: [string]
approval_level: none|confirm|explicit
latency_budget: realtime|interactive|background
privacy_level: local-only|can-escalate
preferred_execution_lane: string   # kept abstract for future cross-node routing
```

---

## Memory Fabric

| Layer | Contents | Canonical Owner |
|-------|----------|-----------------|
| Turn memory | transcript + immediate response state | Hopper (during active turn) |
| Session memory | recent exchanges, active objective, current task/thread | Turing |
| Runtime memory | high-signal events from live work, candidate material for promotion | AIKB runtime pipeline |
| Canonical memory | AIKB docs, state, approvals, runbooks, project history | AIKB git repo |
| Future learned memory | personalization and tuning artifacts | Only after governance is mature |

---

## Tool Fabric

| Group | Examples | Policy |
|-------|----------|--------|
| 1 — Safe read | AIKB reads, status inspection, dashboards, summaries | No approval needed |
| 2 — Low-risk write | note capture, queue creation, non-destructive task updates | Confirm recommended |
| 3 — Action tools | home control, service restarts, remote commands, automation triggers | Explicit confirm required |
| 4 — High-impact | infra changes, destructive ops, external communication, financial/security consequences | Two-step required |

---

## Endpoint Trust Levels

| Level | Surfaces | Capabilities |
|-------|----------|-------------|
| 1 — Watch / wearable | Pixel Watch | short status, quick note capture, stop/cancel, low-risk approvals only |
| 2 — Phone / handheld | Android phone | broader query surface, safe control actions, richer approvals |
| 3 — Desktop / workstation | laptop/desktop | full interaction, planning, deep queries, high-impact workflow initiation |
| 4 — Room satellite | future room devices | voice status, home control, briefings; lower-trust for destructive actions |

---

## Voice Components

### Wake / Interrupt Layer
- `openWakeWord` for local wake-word detection (`Kyloch` or training-friendly fallback phrase)
- dedicated local interrupt path for `stop`, `cancel`, `mute`, and barge-in while TTS is speaking
- this path must not depend on the main LLM

### STT Layer
- `faster-whisper` with `whisper-large-v3-turbo` as the default quality lane
- smaller/faster fallback lane added later, only after the baseline feels solid
- `MacWhisper` is useful as a desktop UX client and experimentation surface, but it is not the system boundary. Kyloch should own the voice session contract so phone, watch, car, Raspberry Pi, and other endpoints all speak to the same gateway.
- Keep STT backend selection abstract behind the gateway. Prefer reusable self-hosted engines first, with platform-native or cloud STT added only where a specific endpoint benefits.

### TTS Layer — Two-lane strategy
**Baseline lane:** low-latency local TTS for everyday replies; favored for interruptibility and responsiveness; used on always-on devices and hot-path answers.

**Premium lane:** `chatterbox` as the branded Kyloch voice lane.
- best for: briefings, narrated summaries, identity-building demo flows, premium replies when latency budget allows
- do not make `chatterbox` the day-one dependency for wake-word, interruption-critical loops, or every room device

### Voice Gateway (Hopper internal sub-services)
- `voice-gateway-api` — inbound audio and text receive, session coordination
- `wake-engine` — `openWakeWord` + VAD + barge-in
- `stt-service` — `faster-whisper` adapter
- `tts-service` — baseline and premium lanes
- `router-service` — Tier 1 orchestrator, Turing handoff decisions
- `session-cache` — short-lived voice turn state

### Endpoint implementation notes
- `Pixel 10 Pro Fold` should be the first non-desktop reference client because it is the most available mic and control surface.
- `Pixel Watch 4` should stay constrained to short commands, note capture, stop/cancel, and low-risk approvals rather than full conversational load.
- Truck and room satellites should favor `Raspberry Pi` class nodes for richer audio and control loops; `ESP32` nodes are best reserved for wake word, push-to-talk, simple transport, sensors, and presence cues.

---

## API Surface

### Hopper voice gateway
```
POST /voice/sessions                  — create a voice session
POST /voice/sessions/:id/audio        — send audio chunk
POST /voice/sessions/:id/text         — send text (push-to-talk fallback or testing)
POST /voice/sessions/:id/interrupt    — barge-in or stop
GET  /voice/sessions/:id/events       — SSE stream of turn events
POST /voice/tts                       — synthesize speech (standalone)
POST /voice/stt                       — transcribe audio (standalone)
```

### Turing control plane
```
POST /kyloch/sessions/register        — register a device session
POST /kyloch/sessions/:id/handoff     — transfer session to another device
POST /kyloch/route                    — route a task packet
POST /kyloch/tools/execute            — execute a tool call through the gateway
GET  /kyloch/briefing                 — AIKB-backed status briefing
GET  /kyloch/approvals                — list pending approvals
POST /kyloch/approvals/:id/respond    — approve or reject a pending action
GET  /kyloch/devices                  — list registered devices
GET  /kyloch/contracts                — return current schema contracts
```

### Event types (SSE stream)
```
wake_detected
listening_started
speech_transcribed
route_selected
tool_call_started
tool_call_finished
response_started
response_audio_chunk
interrupted
handoff_ready
approval_required
```

---

## Session Model
Every endpoint interaction maps onto a shared session object on Turing.

```yaml
session_id: string
user_id: string
device_id: string
endpoint_type: desktop|phone|watch|tv|room|car
mode: desk|mobile|watch|room|car
state: idle|listening|thinking|speaking|awaiting_approval
active_tools: [string]
recent_turn_summary: string
handoff_token: string
last_audio_route: string
latency_metrics: object
```

Session rules:
- one primary active voice session per user by default
- endpoints can attach/detach cleanly
- device handoff preserves the short recent context window
- session continuity survives endpoint reconnects

---

## Control Plane Responsibilities (Turing)
The Turing control plane owns:
- session truth
- task packet routing registry
- device registry
- model registry
- approval registry
- tool policy rules
- AIKB retrieval services
- async task queue coordination
- observability

This keeps Hopper from becoming an accidental monolith.

---

## Model Registry
Kyloch needs a formal model registry, not just "whatever is installed."

```yaml
model_id: string
role: string              # orchestrator|conversational|reasoning|coding|embedder|reranker|stt|tts-baseline|tts-premium
host: string              # hopper|turing
runtime: string           # ollama|llama.cpp|faster-whisper|chatterbox|etc
warm_state: hot|cold
latency_profile: realtime|interactive|batch
cost_class: free|cheap|metered
privacy_class: local-only|can-escalate
tool_call_capable: bool
preferred_task_classes: [A|B|C|D|E]
fallbacks: [model_id]
```

Current model role table → [`kyloch-implementation-roadmap.md`](kyloch-implementation-roadmap.md#model-role-table-to-finalize)

---

## Queue and Async Fabric
You do not need a giant distributed system on day one, but the architecture must admit one.

Minimum useful shape:
- one lightweight queue for deferred tasks
- one worker abstraction that can process tasks off the hot path
- task status visible in the AI Hub operator-console

Add this early enough that long work is not hardcoded into request-response flows.

---

## Observability
Measure the fabric as a system, not as individual endpoints.

Metrics to capture per turn:
- STT latency
- route decision latency
- tool call latency
- specialist escalation rate
- TTS start latency
- interruption success rate
- handoff success rate
- per-endpoint failure causes
- cloud escalation frequency

Append-to-JSONL is sufficient at first. Without this, optimization decisions will be driven by anecdote.

---

## Deployment Shape

### Hopper services
```
kyloch-voice-gateway
kyloch-stt             (faster-whisper)
kyloch-tts-baseline
kyloch-tts-premium     (chatterbox)
kyloch-router
```
Optional: Redis or lightweight queue for streaming/session coordination.

### Turing services
```
ai-hub / operator-console (existing, with Kyloch control-plane backend extensions)
kyloch-session-service
kyloch-tool-gateway
kyloch-memory-bridge
kyloch-device-registry
```

### Home Assistant integrations
- Wyoming endpoints or custom HA integration for room satellites
- notifications and presence/device context
- scripted actions and approvals

---

## Latency Budget Guidance
Do not chase "human perfect" latency first. Aim for predictable responsiveness.

| Path | Target feel |
|------|-------------|
| Wake-word detection | Effectively immediate |
| Interrupt / stop | Immediate, local — never blocked by the LLM |
| Short-command STT | Fast enough to feel conversational |
| Common status answer (hot path) | Responsive with no long dead air |
| Premium narrated reply | Allowed to be slower — use `chatterbox` here |

Keep hot-path answers on the baseline TTS lane. Reserve `chatterbox` for premium moments until measured latency proves it can hold the hot path.

---

## Build Order

### What to build first
1. **Session and task model** — everything depends on shared concepts of sessions, task classes, and routing
2. **Turing control-plane APIs** — gives every future endpoint and Hopper service a common brain to talk to
3. **Hopper front-door runtime** — proves the hot path while respecting the system architecture
4. **One desktop endpoint** — easiest place to validate the system with the richest debugging surface
5. **Specialist routing** — only after the control plane and hot path exist

### What to delay on purpose
- Custom room hardware — easiest way to spend time on packaging while the fabric is still unstable
- TV-first UX — low leverage compared to desktop/phone/watch
- Split inference / KV-cache experiments — architecturally interesting, not required to prove routing
- Multi-user identity — single-operator trust and permissions must be correct first
- Premium-voice dependence — beautiful TTS should not become a blocker for baseline responsiveness

---

## Design Traps

Things most likely to paint Kyloch into a corner:
- Building the first client as if it owns session state
- Mixing Hopper hot-path logic with Turing control-plane policy
- Using frontend-specific request shapes instead of task packets
- Treating model installation as equivalent to model architecture
- Skipping approval classes and trying to add them later
- Hardcoding synchronous request-response for work that should be async
- Letting routing-logic hardening happen before a real Tier 1 model exists (results in a hand-rolled intent parser that becomes entrenched)
- Making `preferred_execution_lane` in task packets too concrete (needs to stay abstract for future cross-node routing)
- Over-optimizing for room hardware before the desk flow is solid
- Assuming watch/TV need equal treatment early

---

## Open Design Questions
- Which wake-word and STT stack provides best local accuracy/latency tradeoff?
- What endpoint protocol will best support low-latency context handoff?
- Which model-routing policy metrics matter most (cost, latency, confidence, sensitivity)?
- What is the minimum useful proactive behavior that feels helpful rather than noisy?
- Voice identity lane: ElevenLabs (cloud + cost + privacy exposure) vs `chatterbox` (local + clonable + unproven at streaming latency under interruption) — must resolve before building the identity layer
- Which workloads are truly better on Apple Silicon vs CUDA once real agent pipelines are measured?
- At what prompt lengths and model sizes does 10 GbE provide enough headroom for split-phase inference?

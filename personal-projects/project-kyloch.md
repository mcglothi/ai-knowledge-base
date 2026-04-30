---
context: personal
tags: [kyloch, jarvis-alias, personal-ai, vision, local-llm, frontier-api, voice, aikb, multi-device]
status: active
last_updated: 2026-04-16
---

# Project Kyloch
**Last Updated:** 2026-04-16
**Summary:** Vision and strategic direction for Kyloch, a personal AI operating layer combining local-first models, selective frontier API use, persistent memory via AIKB, and voice-first multi-device interaction.

---

## Naming Note
- **Canonical name:** Kyloch
- **Historical alias:** Project Jarvis / Jarvis — preserved so older docs and conversations still resolve.

## Vision
Build a personal AI operating system that is:
- **Local-first:** low latency, privacy-preserving, resilient when cloud access is unavailable
- **Hybrid by design:** can escalate to frontier APIs for difficult or high-value tasks
- **Voice-native:** always available through natural speech interactions
- **Context-persistent:** grounded in AIKB memory and recent activity
- **Action-capable:** can automate tools and systems with explicit safety controls

## North Star Experience
- Start a conversation on one device and continue on another without losing context
- Ask for project, life, and home-lab status updates from anywhere
- Delegate tasks to specialized agents (research, scheduling, automation, comms)
- Receive proactive briefings, reminders, and exception alerts
- Approve high-impact actions through a clear and auditable control layer

## Core Architecture (Five Pillars)
1. **Identity + Preference Layer** — personal profile, routines, communication style, mode-aware behavior (home, car, office, mobile)
2. **Memory Layer (AIKB)** — canonical knowledge store, 3-layer memory flow (runtime → candidate → canonical), explainability
3. **Orchestration Layer** — router for local vs. frontier, tool execution, agent coordination
4. **Voice I/O Layer** — wake word, STT, intent parsing, TTS; fast + high-accuracy modes; hard stop and interruption
5. **Endpoint Mesh** — thin clients across home, office, car, and mobile; shared session state and handoff; offline fallback

## Host Role Split
- **Hopper:** front-of-house low-latency runtime (voice, STT, TTS, fast router, conversational model)
- **Turing:** control plane and AIKB-aware orchestration (session registry, tools, approvals, memory bridge)
- **Home Assistant:** endpoint and context fabric (notifications, presence, room devices, mobile/watch integration)

Watch memo capture work is tracked separately in [`pixel-watch-voice-memo.md`](pixel-watch-voice-memo.md) and should feed the same AIKB ideas pipeline.

Full architecture and API contracts → [`kyloch-architecture.md`](kyloch-architecture.md)

## Operating Principles
- **Privacy by default:** local inference and minimal external data transfer
- **Escalate only when needed:** frontier API usage is intentional and policy-driven
- **User-visible control:** permissions, confirmations, and auditability
- **Reliability over novelty:** build from stable workflows and incrementally increase autonomy

## Current Planning Pain Point
Rapid model/tool releases create decision churn that can reset architecture thinking and reduce execution momentum.

Approach:
- Keep core architecture contracts and host role split stable.
- Time-box experiments and evaluate them separately from committed build work.
- Use a fixed review cadence to adopt/reject tooling changes intentionally.

See: [`kyloch-ops-loop.md`](kyloch-ops-loop.md)

## Safety & Trust Model
- Scoped permissions per tool and endpoint
- Two-step confirmation for high-impact actions
- Immutable action and decision logs
- Memory editing controls (inspect, correct, delete)
- No voice biometrics required for v1 — explicit device registration is sufficient

## Hardware Strategy
### Phase 0 (now)
Use existing phone + desktop + Hopper + Turing. Validate UX patterns before buying dedicated hardware.

### Phase 1 (starter hardware)
Preferred first major hardware purchase: MacBook Pro with M5 Max, 128 GB unified memory. One room endpoint with quality mic + speaker. Car integration: phone-led hands-free first.

### Phase 1.5 (heterogeneous AI lab)
Add Nvidia DGX Spark as a CUDA-native sidecar after Phase 1 workflows are proven. Use the existing home 10 GbE fabric first before investing in higher-speed interconnects. First cluster experiment: prefill on DGX Spark, decode on Apple Silicon over 10 GbE. Delay fabric upgrades until measurements show 10 GbE is the bottleneck.

## Phased Roadmap
- **Phase 1 — Personal Copilot Foundation:** AIKB-connected assistant with voice query and status briefings, calendar/tasks/email integrations, local-first model routing with API fallback
- **Phase 2 — Multi-Device Continuity:** session handoff home ↔ office ↔ mobile ↔ car, unified notifications and approvals, endpoint-specific behaviors
- **Phase 3 — Proactive Assistant:** daily/weekly briefings, anomaly alerts, personalized recommendations, expanded automation
- **Phase 4 — Ambient Intelligence:** presence/context-aware behavior, mature multi-agent collaboration, higher autonomy with explicit approval gates

## Initial Build Scope
- AIKB as memory backbone for context and summaries
- Voice query surface for project and home-lab updates
- Lightweight policy router for local vs. frontier model selection
- One automation lane (calendar/tasks) end to end

## Voice Endpoint Strategy
- Treat `MacWhisper` as a strong desktop transcription client and prototyping surface, not the architectural center of Kyloch.
- Build Kyloch around a device-agnostic voice gateway so the same conversation and action fabric can serve the Mac, Pixel 10 Pro Fold, Pixel Watch 4, truck endpoints, and future room devices.
- Prefer reusable STT backends such as `faster-whisper` or `whisper.cpp` for the shared voice service, with platform-native STT or cloud STT used selectively when latency, transport, or device constraints make that the better choice.
- Treat `ESP32` nodes primarily as wake-word, push-to-talk, sensor, and simple audio-edge devices. Use `Raspberry Pi` class hardware for fuller room or vehicle satellite roles where local buffering, playback, and richer device orchestration matter.

### Reference rollout
1. Build one Kyloch voice API that accepts audio or text from any endpoint.
2. Use the desktop path as the first reference client and prototyping lane.
3. Add Android phone support next as the highest-value always-available microphone.
4. Add watch support for short commands, note capture, stop/cancel, and low-risk approvals.
5. Add truck and room endpoints on Raspberry Pi once the core session and routing model is stable.

## Success Criteria
- Voice query-to-answer latency is consistently usable in daily life
- Cross-device context continuity works reliably
- High-impact actions are always user-confirmed and auditable
- System remains useful even during internet/API disruption

## Related Docs
- System architecture, API contracts, session model → [`kyloch-architecture.md`](kyloch-architecture.md)
- Execution plan, phases, design review, changelog → [`kyloch-implementation-roadmap.md`](kyloch-implementation-roadmap.md)
- Operating cadence to prevent tool-churn resets → [`kyloch-ops-loop.md`](kyloch-ops-loop.md)
- AI services and consulting business direction → [`../personal/ai-services-business.md`](../personal/ai-services-business.md)

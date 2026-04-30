---
context: personal
tags: [kyloch, jarvis-alias, architecture, failure-contract, hopper, turing, reliability]
status: active
last_updated: 2026-04-18
---

# Kyloch Failure Contract

**Last Updated:** 2026-04-18
**Summary:** Defines failure modes, degradation paths, and recovery behavior for Hopper (front-of-house runtime) and Turing (control plane/memory). Written before Phase 2 Hopper runtime wiring to prevent ambiguous behavior under partial outages.

---

## Guiding Principle

Kyloch must **never leave the user in an ambiguous state**. When something fails, the system should either:
1. Handle it transparently (degrade gracefully), or
2. Tell the user clearly what happened and what to do

No silent failures, no hanging states, no "it's thinking..." when nothing is happening.

---

## Host Failure Modes

### Hopper Fails (Front-of-House Runtime)

**Symptoms:** Voice gateway unresponsive, STT/TTS down, router unreachable on `10.10.10.200`

| Scenario | Behavior | Recovery |
|----------|----------|----------|
| Hopper fully unreachable (network down, power loss) | Voice endpoints detect connection failure within 5s. Fall back to text-only mode via Turing web UI. No voice path available until Hopper returns. | Auto-recovery: when Hopper comes back, voice gateway auto-registers with Turing control plane. Existing sessions are lost (Hopper owns turn state only). |
| Hopper OOM / crash loop | Tier 0 (wake word, VAD, interrupt) continues working — these are local, non-LLM. Router service crashes → no voice-to-text processing. STT/TTS containers crash but can be restarted independently. | Systemd restart policies should apply to individual services, not the whole host. If host is locked (like 2026-04-03 incident), JetKVM + WoL + external power control needed for recovery. |
| Hopper degraded (high CPU, slow responses) | Router service detects latency > 2s and marks itself as degraded. New voice sessions are rejected with a clear error. Existing sessions complete but no new ones accepted. | Degraded mode should be visible in Turing operator-console. User gets a status card: "Hopper is slow — voice temporarily unavailable, use text mode." |
| Hopper network partition (can reach Turing but not endpoints) | Voice gateway can route to Turing for memory/tool work, but cannot receive audio from endpoints. Endpoints see connection refused. | Turing detects Hopper heartbeat loss after 10s. Marks Hopper as unreachable in device registry. |
| Hopper network partition (can reach endpoints but not Turing) | Voice gateway processes STT locally, has Tier 1 model for basic responses. Cannot access AIKB memory, cannot call tools requiring Turing approval. | Falls back to local-only mode: Tier 1 model handles B-class tasks (simple conversation, status). C-class tasks (memory-grounded) return "I can't access my notes right now." D/E tasks are queued for when Turing returns. |

**Key decision: When Hopper is unreachable from Turing, does Hopper degrade to local-only, queue tasks, or fail hard?**

**Answer: Local-first with clear degradation.** Hopper should always be able to handle B-class tasks (fast conversational) using its local Tier 1 model. C-class tasks degrade to "I need my control plane." D/E tasks are queued in Hopper's local cache and replayed when Turing returns.

### Turing Fails (Control Plane / Memory)

**Symptoms:** Control plane APIs unreachable, session registry down, AIKB retrieval unavailable on `10.10.10.50`

| Scenario | Behavior | Recovery |
|----------|----------|----------|
| Turing fully unreachable | Hopper continues processing voice locally. Tier 1 model handles B-class tasks. C-class (memory) and D-class (specialist) tasks are queued locally with a clear message: "I'm working offline — I'll remember this and process it when I reconnect." | When Turing returns, Hopper replays queued tasks. Session state from the offline period is merged into Turing's session registry. |
| Turing API slow / high latency | Hopper detects response > 3s from Turing APIs. Switches to optimistic local mode: processes tasks locally, syncs with Turing when it responds. | No data loss — Hopper's local queue is the source of truth during partition, Turing reconciles on reconnect. |
| Turing disk full / database corruption | Control plane is down but Hopper continues in local-only mode. Operator must fix Turing before Kyloch regains memory/tool capabilities. | Hopper should have a health-check endpoint that reports "Turing unreachable" status to voice endpoints. |
| Turing memory layer corrupted (AIKB) | Hopper continues with Tier 1 model for B-class tasks. C-class tasks return generic responses without AIKB grounding. | AIKB is git-backed — recovery is `git pull`. Memory pipeline can rebuild runtime events from the last good state. |

**Key decision: Turing owns session state, but during partition Hopper must be able to function independently.**

**Answer: Hopper is the always-available layer. Turing is the memory/control enhancement.** This means Hopper's Tier 1 model must be capable of useful conversation without Turing. Turing enriches the experience but doesn't block basic functionality.

### Home Assistant Fails (Endpoint / Context Fabric)

| Scenario | Behavior | Recovery |
|----------|----------|----------|
| HA unreachable | Notifications stop. Presence/context signals unavailable. Low-risk home-control actions via HA are blocked. Phone/watch paths continue working (they don't depend on HA). | No degradation to core Kyloch functionality. Only context enrichment is lost. |
| HA partial (some integrations down) | Affected devices show as unavailable in Turing device registry. Other devices continue normally. | HA auto-recovery — no special Kyloch handling needed since HA is treated as a first-class integration, not a structural dependency. |

---

## Tier Failure Modes (Within Hopper)

| Tier | Failure | Behavior |
|------|---------|----------|
| Tier 0 (wake word, VAD) | Fails | No wake-word detection. User must use push-to-talk or text input. **This is the most critical failure — Tier 0 MUST have no LLM dependency.** |
| Tier 1 (router/orchestrator) | Fails | No voice processing. System falls back to Turing web UI text mode. STT/TTS may still work as standalone services but no routing occurs. |
| Tier 2 (specialist) | Fails | D-class tasks return "I can't do that right now" instead of hanging. No impact on B/C-class tasks. |
| Tier 3 (async workers) | Fails | Queued tasks accumulate in Hopper's local queue. No proactive briefings or background scans until workers recover. |

---

## Network Partition Scenarios

### Scenario A: Hopper ↔ Turing partition (most likely)
- **Hopper behavior:** Local-only mode. Tier 1 model handles B-class tasks. C/D/E tasks queued locally.
- **Turing behavior:** Detects Hopper heartbeat loss after 10s. Marks Hopper as unreachable. Existing sessions from other endpoints continue normally.
- **User experience:** "Voice is working offline — I can answer basic questions but can't check my notes or run tools."
- **Recovery:** When partition heals, Hopper replays queued tasks and syncs session state to Turing.

### Scenario B: Endpoint ↔ Hopper partition
- **Endpoint behavior:** Detects connection failure. Falls back to text input or waits for reconnection.
- **Hopper behavior:** Unaffected — continues serving other endpoints.
- **User experience:** "Connection lost" on the endpoint device. No voice input available until reconnected.

### Scenario C: Endpoint ↔ Turing partition (Hopper reachable)
- **Endpoint behavior:** Voice goes through Hopper → Tier 1 handles locally. Turing-dependent features unavailable.
- **Hopper behavior:** Processes as local-only mode (same as Scenario A from Hopper's perspective).
- **User experience:** Same as local-only mode.

---

## Recovery Procedures

### Hopper Recovery (from lockup/crash)
1. **Auto-recovery:** Systemd restart policies for individual services (voice-gateway, stt-service, router-service)
2. **Partial recovery:** If host is responsive but services are down, `systemctl restart kyloch-*`
3. **Full recovery:** If host is locked (like 2026-04-03), use JetKVM + WoL + external power control for hard reset
4. **Post-recovery:** Hopper auto-registers with Turing, replays any queued tasks from local cache

### Turing Recovery (from crash/corruption)
1. **Service restart:** `systemctl restart ai-hub` or relevant service
2. **Memory recovery:** AIKB is git-backed — `git pull` to restore canonical docs
3. **Runtime recovery:** Memory pipeline rebuilds runtime events from last good state
4. **Session recovery:** Hopper's local queue is replayed when Turing returns

### Network Partition Recovery
1. **Detection:** Heartbeat monitoring (10s timeout) on both Hopper and Turing
2. **State reconciliation:** When partition heals, Hopper sends queued tasks to Turing
3. **Session merge:** Turing merges Hopper's offline session state into canonical registry
4. **Notification:** Operator-console shows "X tasks processed during outage" summary

---

## Monitoring & Alerting

### What to monitor
- Hopper heartbeat (every 5s, timeout 10s)
- Turing API health (every 10s, timeout 5s)
- Tier 1 model latency (per-request)
- Queue depth on Hopper (alert if > 5 pending tasks)
- STT/TTS service status (every 30s)

### Alert thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Hopper heartbeat missed | 1 miss (5s) | 2 consecutive misses (10s) |
| Turing API latency | > 2s | > 5s or timeout |
| Queue depth | > 3 pending tasks | > 10 pending tasks |
| Tier 1 model latency | > 3s p95 | > 10s p95 |

---

## Design Constraints (Non-Negotiable)

1. **Tier 0 never depends on LLM** — wake word, VAD, interrupt must work even if the entire system is down except the audio stack
2. **Hopper can function without Turing** — local Tier 1 model must handle B-class tasks independently
3. **Turing can function without Hopper** — other endpoints (desktop, web UI) must work if Hopper is down
4. **No silent failures** — every failure mode has a user-visible state and recovery path
5. **Session state is eventually consistent** — Hopper's local queue is source of truth during partition, Turing reconciles on reconnect
6. **Recovery is automated where possible** — systemd restarts, auto-registration, queue replay

---

## Open Questions (to resolve before Phase 2)

1. **What is the exact heartbeat interval and timeout?** (Proposed: 5s check, 10s timeout)
2. **How long should Hopper keep queued tasks?** (Proposed: 24 hours, then discard with notification)
3. **Should Hopper have a "safe mode" that limits tool access during degraded operation?** (Yes — no tool calls when Turing is unreachable)
4. **What happens to active voice sessions during a Hopper crash?** (Lost — Hopper owns turn state. This is acceptable because Tier 0 interrupt always allows graceful session end.)
5. **Should we add a third fallback node for critical services?** (No — over-engineering for day one. Single Hopper + single Turing is sufficient if failure contracts are solid.)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-04-18 | Initial draft — written before Phase 2 Hopper runtime wiring. Covers all host failure modes, network partitions, recovery procedures, and monitoring thresholds. |

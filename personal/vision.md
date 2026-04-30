---
context: personal
---
# Visionary Goals

**Last Updated:** 2026-03-22
**Summary:** Ideas and longer-horizon goals worth preserving but not yet active projects. These are concepts to revisit when current priorities allow.

---

## Ambient AI / Voice-Aware AIKB

**The vision:** Agents (Claude Code, Gemini, etc.) work on projects in the background, updating AIKB as they go. At any point — from phone or a home voice device — you can ask for a status update or approve pending actions.

**Key components needed:**
1. **Structured approval file** — agents write to `_pending_approvals.md` instead of acting autonomously on decisions that warrant human sign-off. Voice interface reads it on demand.
2. **AIKB bridge** — a service that queries the AIKB GitHub repo in real-time (GitHub API) at the moment of a voice query, so responses are always current. Could run on feynman or as a Cloud Run function.
3. **Voice interface** — two surfaces:
   - **Pixel (mobile):** Gemini Live supports real-time function calling — most promising path, no extra hardware
   - **Home:** Google Home/Nest speakers, or Home Assistant with Claude/Gemini API integration
4. **Notification layer** — agents push a notification (ntfy, Pushover, etc.) when something needs approval, rather than requiring proactive queries

**Why the AIKB structure suits this well:**
- Git repo = any agent can write, changes are versioned and auditable
- GitHub API = queryable without special infrastructure, always fresh
- Flat markdown files = easy to parse and summarize for voice responses

---

## HA Command Center (Tony Stark Aesthetic)

**The vision:** A high-end, information-dense HUD for the home lab, bridging infrastructure monitoring with custom automation.

**Key components:**
1. **Infrastructure HUD:** Real-time thermals, network throughput, and energy usage (TrueNAS, Pi-hole, Sense) on a single "Bubble Card" pane of glass.
2. **OpenSoak Bridge:** FastAPI to HA REST sensors. "Ready for Soak" scene: sets Denon audio, patio lights, and verifies tub temperature.
3. **Hardware Fail-safes:** Z-Wave leak sensors under the rack and spa linked to a "Main Power Kill" scene.

---

## Ambient Assistant (Doc Brown's Garage)

**The vision:** Digital Rube Goldberg machines that anticipate needs through presence and context.

**Key components:**
1. **Presence Awareness:** Room-level tracking (ESPPresence or Bluetooth) to adjust audio/lighting dynamically.
2. **AIKB Voice Bridge (Jarvis):** Custom HA integration allowing voice queries against AIKB documents (e.g., "Jarvis, what's the pinout for the heater?").
3. **The "Morning Briefing":** Sit-down trigger that reads out `_pending_approvals.md` and a summary of lab health.

**Status:** ⬜ Stashed — Revisit when HACS and basic HA dashboarding are stabilized.

---

## Local LLM Benchmark Playback Explorer

**The vision:** A website that turns local-LLM benchmark data into an experiential preview so buyers can feel the difference between hardware, models, and quantizations before purchasing.

**Key components:**
1. **Benchmark corpus:** Collect prompt-processing, generation, and time-to-first-token measurements across hardware, model, quantization, backend, and context sizes.
2. **Playback simulator:** Use a small set of pre-recorded prompts and answers with variable lengths so the UI can replay realistic waits, first-token latency, and streamed output at the measured speeds.
3. **Scenario presets:** "Chat reply", "long code answer", "RAG with big prompt", and "slow CPU fallback" presets that reveal where prefill vs decode performance matters.
4. **Buyer framing:** Translate raw tokens/sec into practical labels like "feels instant", "feels like typing", and "good for overnight batch jobs, not interactive chat".
5. **Differentiator:** Existing local-AI benchmark sites show numbers and leaderboards, but the opportunity is to make those numbers legible to non-experts through interactive simulation.

**Status:** ⬜ Stashed — promising product/affiliate angle if paired with trustworthy methodology and community-submitted runs.

---

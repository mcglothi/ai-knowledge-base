---
tags: [kyloch, jarvis-alias, operating-model, roadmap, experimentation, decision-hygiene, architecture]
status: active
last_updated: 2026-04-27
---

# Kyloch Operating Loop (Anti-Reset System)
**Last Updated:** 2026-04-27
**Summary:** A practical operating model to prevent architecture churn from daily tool/model releases while preserving experimentation speed.

---

## The Core Problem
Kyloch is a long-horizon system. AI tooling changes weekly. Without a decision framework, every new model/tool can reset planning and erase momentum.

This loop creates a **stability spine + experimentation edge**.

---

## 1) Use a Two-Speed System

### A. Stability Spine (slow-changing, quarterly)
These should change rarely:
- session/task contracts
- host role split (Hopper vs Turing responsibilities)
- trust/approval model
- memory lifecycle (runtime → candidate → canonical)
- endpoint capability tiers

Rule: only revise spine decisions during scheduled architecture reviews, not ad hoc.

### B. Experimentation Edge (fast-changing, daily/weekly)
These can change often:
- model candidates
- STT/TTS engines
- routing heuristics
- tool wrappers and adapters
- UI clients and convenience surfaces

Rule: experiments are expected to churn. Spine is not.

---

## 2) Organize Work into Three Queues

## A. Build Queue (Committed)
- items currently being implemented
- strict WIP limit: max 3 active items
- each item must have clear exit criteria

## B. Evaluation Queue (Time-boxed)
- candidate tools/models to test
- each gets a 1-page experiment card with:
  - hypothesis
  - test dataset/tasks
  - success criteria
  - stop date
  - adopt/hold/reject decision

## C. Parking Lot (Not now)
- interesting ideas captured so they stop consuming working memory
- revisit during weekly review only

---

## 3) Add a Tool-Churn Shield

For every “new hot tool,” score 1–5 on:
- **Leverage** (how much Kyloch capability improves)
- **Integration Cost** (time + complexity)
- **Lock-in Risk**
- **Reliability in your environment**
- **Reversibility**

Adoption gate:
- require total score threshold + one clear use case + rollback path
- if no clear rollback path, do not adopt into core

Default policy:
- **Observe first, adopt second** (7-day cooling period)

---

## 4) Decision Half-Life (prevents stale assumptions)

Every architecture/tool decision gets:
- decision date
- owner
- rationale
- review date (30/60/90 days)
- reversal trigger (what evidence would make you change it)

This removes the “everything might be wrong now” anxiety because decisions are intentionally revisitable.

---

## 5) Daily / Weekly Rhythm

### Daily (15 minutes)
1. Check Build Queue (what is the next executable step?)
2. Capture any new shiny tool into Evaluation Queue (not Build Queue)
3. Send yourself one “today’s focus” line

### Weekly (45 minutes)
1. Review experiment results
2. Promote at most 1 experiment into Build Queue
3. Archive/reject weak candidates
4. Reconfirm top 3 priorities for Kyloch

### Monthly (60–90 minutes)
1. Architecture review window
2. Revisit only Stability Spine decisions due for review
3. Update roadmap based on evidence, not hype

---

## 6) AI Agent Roles (recommended)

- **Goose (interactive PM + editor):**
  - maintain queues
  - produce weekly synthesis
  - update roadmap docs and AIKB state

- **Hermes (always-on operations):**
  - monitor stale projects/blockers
  - send scheduled nudges (Telegram/Signal)
  - trigger reminder workflows

- **OpenClaw (approval/control surface):**
  - run/approve sensitive automation actions safely

---

## 7) Minimal Message Format for Daily IM Nudges

Morning:
- Top 3 today
- 1 blocker needing decision
- 1 experiment to ignore this week

Evening:
- What moved to done
- What remains blocked
- Next first step for tomorrow

---

## 8) What “Done” Means for This System
- Kyloch decisions no longer reset from every new release
- experiments are captured without hijacking build momentum
- project status is externally visible (digest) instead of mentally tracked
- architecture changes happen on cadence, not impulse

---

## Related
- [`project-kyloch.md`](project-kyloch.md)
- [`kyloch-architecture.md`](kyloch-architecture.md)
- [`kyloch-implementation-roadmap.md`](kyloch-implementation-roadmap.md)

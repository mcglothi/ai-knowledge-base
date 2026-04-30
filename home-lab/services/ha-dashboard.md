---
context: personal-homelab
tags: [home-assistant, lovelace, dashboard, mushroom, bubble-card, hacs, frontend, ui]
hosts: [babbage]
last_updated: 2026-03-01
---

# Home Assistant Dashboard

**Last Updated:** 2026-03-01
**Summary:** Design research and implementation plan for the Home Assistant Lovelace dashboard refresh.
**Status:** ⚠️ IN PROGRESS — design decisions pending (tablet hardware + layout)

## Overview

Planning a SOTA Lovelace dashboard for `lovelace.home.timmcg.net`. Research complete, design options evaluated. Awaiting decisions before building.

---

## Devices in HA (known so far)

- **Z-Wave (HUSBZB-1):** lights, sensors, thermostat (mixed device types)
- **Denon AVR-X1100W** — HTTP API controllable (IP: 10.10.198.166)
- **Samsung UN55JU6700** — samsungtvws when on; CEC bridge (ESP32) planned for power-on

---

## Design Options Evaluated

### Option A — Mushroom + Sections (Grid Overview)
- **Best for:** desktop/tablet-first, household overview at a glance
- **HACS deps:** `mushroom`, `card-mod`, `auto-entities`
- One main overview page in Sections layout (drag-drop grid)
- Mushroom chips status bar at top (who's home, weather, lights on, lock state)
- Room nav buttons → each room as a section below
- Global "all lights on/off" via auto-entities
- Works great on desktop and tablet; moderate on mobile

### Option B — Bubble Card (Pop-up / Mobile-first) ← **Recommended**
- **Best for:** phone + wall tablet, extremely clean main view
- **HACS deps:** `bubble-card`, `mushroom`
- Single main view with Mushroom chips status bar
- Room buttons on main page → tap → pop-up with full room controls
- Horizontal nav footer (Home / Lights / Climate / A/V / Settings)
- Dominates r/homeassistant in 2025/2026 aesthetics
- Works best across all surfaces (phone, tablet, desktop)

### Option C — Native Areas Dashboard (Zero-code)
- Auto-generated from HA Areas — no HACS required
- Good starting point, limited visual ceiling
- Best if still pairing many devices

---

## Pending Decisions (blocking build)

1. **Wall tablet hardware** — screen size + resolution affects column count and card sizing
2. **Layout choice** — Option A vs B (leaning B per research)
3. **Rooms/Areas** — need full list of areas defined in HA before building nav structure
4. **HACS OK?** — assumed yes, but not confirmed

---

## HACS Frontend Stack (when ready to build)

| Package | Purpose | Install |
|---------|---------|---------|
| `bubble-card` | Pop-up cards + nav footer | HACS Frontend |
| `mushroom` | Status chips + entity cards | HACS Frontend |
| `card-mod` | CSS customization of any card | HACS Frontend |
| `auto-entities` | Dynamic entity lists (e.g. "all lights that are on") | HACS Frontend |

HACS itself requires a GitHub token — retrieve from Vaultwarden: `PAT/GitHub/AIKB MCP Token` (or create a separate one).

---

## Build Plan (when decisions are made)

1. Install HACS on HA container
2. Install frontend packages above
3. Create new dashboard (don't modify default)
4. Set up Areas in HA (one per room)
5. Build main view: chips + room buttons
6. Build per-room pop-ups
7. Build A/V pop-up (Denon + Samsung controls)
8. Build climate pop-up (thermostat)
9. Test on all surfaces (phone, tablet, desktop)
10. Set as default dashboard

---

## Reference Links

- [Bubble Card GitHub](https://github.com/Clooos/Bubble-Card)
- [Mushroom Cards GitHub](https://github.com/piitaya/lovelace-mushroom)
- [Minimalist tablet dashboard example (community)](https://community.home-assistant.io/t/minimalist-home-assistant-tablet-dashboard-with-mushroom-bubble-cards/828470)
- [Mushroom + Sections 2025 write-up](https://www.michaelsleen.com/dashboard-update/)
- [HA Sections view docs](https://www.home-assistant.io/dashboards/sections/)

---
context: personal-homelab
tags: [rgb, feynman, openrgb, systemd, timers, lighting, linux, arch, scripts]
hosts: [feynman]
last_updated: 2026-02-19
---

# RGB Control Automation (feynman)
**Last Updated:** 2026-02-19
**Summary:** Automated control of the **feynman** Arch desktop RGB lighting via OpenRGB and systemd timers. Not applicable to laptops or other workstations.

## Environment Requirements
- **Machine:** `feynman` only — tied to specific RGB hardware in that machine
- **Tools:** `OpenRGB` (CLI), `systemctl`
- **Platform:** Linux / systemd

## Scope
- **Target Machine:** `feynman` (Arch Linux Desktop)
- **Hardware:** Specific to ENE DRAM, GTX 1080 Ti, NZXT Kraken, and Razer peripherals.

## Components
- **Script:** `/home/mcglothi/code/scripts/rgb-control.sh`
- **Tool:** `OpenRGB` (CLI)
- **Profiles:** `~/.config/OpenRGB/last_state.orp` (Saved before turning off)

## Schedule
- **Off:** 8 PM (20:00) daily via `rgb-off.timer`
- **On:** 8 AM (08:00) daily via `rgb-on.timer`
- **Boot:** Automatically restores state on boot/login via `rgb-smart-on.service` (only if between 8 AM and 8 PM).

## Gotchas
- **ENE DRAM:** Requires explicit targeting (`--device "ENE DRAM"`) to turn off reliably.
- **GPU/Kraken:** No dedicated "Off" mode; achieved by setting color to black (`000000`).

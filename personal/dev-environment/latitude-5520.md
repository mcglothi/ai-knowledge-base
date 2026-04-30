---
context: personal
---
# Dev Environment: latitude-5520
**Last Updated:** 2026-02-19
**Summary:** Dell Latitude 5520 — Testbed for various Linux distros. Environment profile varies by current OS install.

---

## Machine Specs

| Item | Value |
|------|-------|
| Model | Dell Latitude 5520 |
| Current OS | ⬜ distro-hopping — check on session |
| Architecture | x86_64 |
| Hostname | ⬜ may vary |

---

## Environment Profile
⚠️ This machine runs different distros over time. The profile below must be verified at session start.

| Variable | Value |
|----------|-------|
| Home directory | `/home/mcglothi/` (assumed for Linux) |
| Code root | `~/code/` (assumed — confirm) |
| Package manager | ⬜ depends on distro (`pacman`, `apt`, etc.) |
| Init system | `systemd` (assumed) |
| Python command | `python3` (version ⬜) |
| Shell | `zsh` (assumed — confirm) |
| Architecture | `x86_64` |

---

## Instructions for AI
**At the start of any session on this machine:**
1. Run `cat /etc/os-release` to identify the current distro.
2. Run `hostname` — note it here if it differs from a prior session.
3. Run `which pacman || which apt || which dnf` to confirm package manager.
4. Run `python3 --version` and `git --version`.
5. Update this file if the OS has changed since the last session.
6. Note if this is a persistent install or a temporary/live setup.

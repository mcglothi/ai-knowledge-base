# Dev Environment

**Last Updated:** YYYY-MM-DD
**Summary:** Machine inventory and per-machine profiles. Agents read this to use correct paths, tools, and package managers.

> **This is an example file.** Copy it to `personal/dev-environment/README.md` and replace with your own machines.
> Then create a `personal/dev-environment/<hostname>.md` for each machine using `_templates/machine-profile.md`.

---

## Machine Quick Reference

| Hostname | OS | Role | Code root | AIKB path |
|----------|----|------|-----------|-----------|
| `my-macbook` | macOS 14 | Primary laptop | `~/Code/` | `~/Code/AIKB/` |
| `my-desktop` | Ubuntu 24.04 | Home workstation | `~/code/` | `~/code/AIKB/` |
| `my-server` | Debian 12 | Home server | `/opt/code/` | N/A — MCP only |

---

## Default Assumptions

When the hostname matches a row above, apply that machine's profile. When the hostname is unrecognized:
1. Run `uname -s` to identify OS (Darwin = macOS, Linux = Linux)
2. Probe for package manager: `which brew || which apt || which dnf || which pacman`
3. Assume code root is `~/Code/` on macOS, `~/code/` on Linux unless a local clone says otherwise

---

## Environment Variables (all machines)

| Variable | Purpose |
|----------|---------|
| `EDITOR` | Default text editor |
| `VISUAL` | Visual editor for git commits |

---

## Per-machine profiles

- [`my-macbook.md`](my-macbook.md) — Primary macOS laptop
- [`my-desktop.md`](my-desktop.md) — Ubuntu home workstation

> Create these files using `_templates/machine-profile.md` and fill in the installed tools list.
> The installed tools list is critical — agents will check it before using any tool.

---
context: personal
---
# Development Environments
**Last Updated:** 2026-04-17
**Summary:** Overview of all machines used for development. Each machine file is an execution profile — it tells an agent what's available and how to operate on that machine. Project files describe what a project needs; machine files describe what's here. Agents compose them at session start.

---

## Machine Index

| Hostname | Type | Details |
|----------|------|---------| 
| **feynman** | Arch Linux Desktop (x86_64) | [`feynman.md`](feynman.md) |
| **tesla** | MacBook Pro M1 13" (arm64) | [`tesla.md`](tesla.md) |
| **mbp-i9** | MacBook Pro i9 15" (x86_64) | [`mbp-i9.md`](mbp-i9.md) |
| **latitude** | Dell Latitude 5520 — distro varies | [`latitude-5520.md`](latitude-5520.md) |

---

## Cross-Machine Quick Reference

Key variables that differ by machine. Resolve these before running any commands.

| Variable | feynman | tesla | mbp-i9 | latitude |
|----------|---------|----------------|--------|----------|
| Home dir | `/home/mcglothi/` | `/Users/mcglothi/` | `/Users/mcglothi/` ⬜ | `/home/mcglothi/` ⬜ |
| Code root | `~/code/` | `~/code/` | `~/code/` ⬜ | `~/code/` ⬜ |
| Package mgr | `pacman` / `yay` | `brew` | `brew` | ⬜ distro-dependent |
| Init system | `systemd` | `launchd` | `launchd` | `systemd` ⬜ |
| Python cmd | `python3` | `python3` / `python3.11` | `python3` ⬜ | `python3` ⬜ |
| Architecture | `x86_64` | `arm64` | `x86_64` | `x86_64` |

⬜ = not yet confirmed on that machine. Verify and update when first active.

---

## Shared Preferences
*These apply across all environments unless overridden in a machine-specific file.*

- **Shell:** zsh (managed via dotfiles)
- **Editors:** Cursor, VS Code, Vim
- **Terminal:** Alacritty (preferred)
- **Dotfiles Repo:** `{code root}/dotfiles` (path varies by machine — see quick reference)
- **Dictation (macOS):** Native macOS Dictation (Hold `Command` key) is the preferred workstation STT method for terminal commands on Apple Silicon. MacWhisper is retained as a GUI fallback for long-form transcription.

---

## macOS Hardware Pre-Purchase Checklist

Mac hardware compatibility is consistently painful — docking stations, displays, 10G adapters, etc. Linux boxes "just work"; macOS does not. **Before recommending or purchasing any hardware for a macOS machine:**

1. **Check vendor's stated macOS support range** — "macOS supported" is not enough. Find the max tested version (e.g. "macOS 12.7–15.4") and compare against the running OS.
2. **newton runs macOS 26.4.1 (Tahoe)** — a pre-release/cutting-edge OS. Many vendors have not tested against it. Assume anything listed as "macOS 15.x max" is unverified on Tahoe.
3. **For networking adapters:** check whether the chipset's macOS driver exposes the needed media types (optical vs copper). Apple's native drivers (Aquantia, etc.) often only expose copper BASE-T even on SFP+ hardware.
4. **Check community reports** for the exact chipset + macOS version combo, not just the product page marketing copy.
5. **Prefer adapters with vendor-maintained macOS drivers** (e.g. Sonnet, OWC) over adapters that rely solely on Apple's built-in drivers.

Lesson learned 2026-04-17: QNAP QNA-UC10G1SF (AQC107) returned after discovering Apple's Aquantia driver has no optical SFP+ support on Tahoe. Replaced with Sonnet Solo 10G SFP+.

---

## Agent Orientation Protocol

At the start of any session that may involve running commands:

1. **Identify the machine:** Run `hostname`. Match it to the table above.
2. **Load the machine file:** Read the corresponding file in this directory for its full Environment Profile (package manager, home dir, installed/absent tools).
3. **Apply the profile:** Use the machine's package manager, paths, and Python command for all commands in the session. Do not assume a tool is available unless it's listed in the machine file's "Installed Tools" section.
4. **Check project requirements:** If working on a project, compare its `Environment Requirements` section against the machine profile. Flag any gaps before starting.

### Hostname alias note
- `tesla` now resolves directly to [`tesla.md`](tesla.md) for hostname-based lookup consistency.
- [`mbp-m1.md`](mbp-m1.md) remains as the legacy canonical content file so older links do not break.

---

## New Machine Bootstrap

To get AIKB and Claude Code working on a new machine from scratch:

**Prerequisites:** Claude Code installed, `bw` configured and logged in to `vault.home.timmcg.net`

```bash
# 1. Get the GitHub token from Vaultwarden
export GITHUB_PERSONAL_ACCESS_TOKEN=$(bw get password "PAT/GitHub/AIKB MCP Token" --session "$(cat ~/.bw_session)")

# 2. Configure the GitHub MCP server
# IMPORTANT: the server-github package requires GITHUB_PERSONAL_ACCESS_TOKEN, NOT GITHUB_TOKEN
claude mcp add github-aikb -s user \
  -e "GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN" \
  -- npx -y @modelcontextprotocol/server-github

# 3. Fetch CLAUDE.md from AIKB via GitHub API (no local clone needed)
curl -s -H "Authorization: Bearer $GITHUB_PERSONAL_ACCESS_TOKEN" \
  "https://api.github.com/repos/mcglothi/AIKB/contents/_agents/claude-code.md" | \
  python3 -c "import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" \
  > ~/.claude/CLAUDE.md

# 4. Fetch GEMINI.md from AIKB (for Gemini CLI)
curl -s -H "Authorization: Bearer $GITHUB_PERSONAL_ACCESS_TOKEN" \
  "https://api.github.com/repos/mcglothi/AIKB/contents/_agents/gemini-cli.md" | \
  python3 -c "import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" \
  > ~/.gemini/GEMINI.md

# 5. Configure Gemini CLI MCP
gemini mcp add github-aikb -s user -e "GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN" npx -y @modelcontextprotocol/server-github

# 6. Launch Claude — AIKB is now accessible via MCP
claude
```

At this point Claude Code will be in MCP mode. If the machine is a keeper (not a temp VM), clone the repo during or after the first session so future sessions use local mode:

```bash
git clone https://github.com/mcglothi/AIKB.git {code_root}/AIKB/
```

Then sync CLAUDE.md from the clone going forward:
```bash
cp {code_root}/AIKB/_agents/claude-code.md ~/.claude/CLAUDE.md
```

---

### Unrecognized machine (temp VM or new machine)
If `hostname` doesn't match any machine in the index:
1. Run `uname -s && uname -m` (OS and architecture).
2. Run `which pacman || which apt || which dnf || which brew` to identify package manager.
3. Run `python3 --version && git --version`.
4. Build a working environment profile in memory from these results.
5. If the session is substantial, create a machine file: `personal/dev-environment/<hostname>.md` using the existing files as a template.
6. Note any gaps between what the project needs and what's available before proceeding.

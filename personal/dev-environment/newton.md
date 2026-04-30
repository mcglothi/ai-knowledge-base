---
tags: [newton, macbook-pro, apple-silicon, m5-max, dev-environment]
last_updated: 2026-04-22
---

# Dev Environment: newton
**Last Updated:** 2026-04-22 (rev 6)
**Summary:** MacBook Pro M5 Max, 128 GB RAM, 3.6 TB SSD. macOS 26.4.1 (Tahoe). Primary workstation replacement. Hostname: `newton`. Tailscale IP: `100.64.0.6`.

---

## Maintenance Log
| Date | Action | Status |
|------|--------|--------|
| 2026-04-24 | **DNS Optimization:** Added `newton10g.home.timmcg.net` to primary Pi-hole DNS (`10.10.10.10`). Verified resolution and low-latency connectivity from `feynman`. | ✅ |
| 2026-04-24 | **Networking Strategy:** Restored static IP `10.10.110.110` for 10G interface as `newton10g`. Wi-Fi remains active alongside 10G. Removed Hammerspoon auto-toggle to prevent manual switching overhead. | ✅ |
| 2026-04-24 | **Automation & Services:** Aliased `tailscale` in `.zshrc`. Verified `LM Studio` (v0.3.x) is primary local runtime. | ✅ |
| 2026-04-21 | **Docking Strategy Finalized:** Purchased OWC Thunderbolt 5 Hub and Sonnet Solo 10G SFP+ adapter. Transitioning to a single-cable lab docking solution (Newton Lab Dock). | ✅ |
| 2026-04-20 | **Migration complete:** Replaced Homebrew Tailscale daemon with Tailscale standalone app (v1.96.5). Registered on headscale at `hs.timmcg.net` as `newton` (100.64.0.6). `accept-routes` and `accept-dns` enabled via app settings. Removed `/etc/resolver/home.timmcg.net` workaround; split DNS now correctly handled by Tailscale Network Extension. | ✅ |
| 2026-04-16 | Initial bootstrap: Tailscale installed via Homebrew, daemon configured as system LaunchDaemon (`/Library/LaunchDaemons/com.tailscale.tailscaled.plist`), registered on headscale at `hs.timmcg.net` (100.64.0.5). | ✅ |
| 2026-04-16 | GitHub/git auth configured: `gh` CLI logged in with shared token, `~/.gitconfig` copied from tesla, `id_rsa` + `svc_*` SSH keys copied from tesla, GitHub added to `known_hosts`. | ✅ |
| 2026-04-16 | Shell environment bootstrapped: oh-my-zsh installed, `powerlevel10k` theme + `~/.p10k.zsh` copied from tesla, `zsh-autosuggestions` and `zsh-syntax-highlighting` plugins installed. `~/.zshrc` copied from tesla. | ✅ |
| 2026-04-16 | Bitwarden CLI installed (`bw 2.x` via brew), vault server configured to `vault.home.timmcg.net`. `bwu`/`bws` functions available via `.zshrc`. Session requires one-time `bwu` to generate `~/.bw_session`. | ✅ |
| 2026-04-16 | AIKB cloned to `~/code/AIKB`, upstream synced to `2ad1c19`, `.aikb-config.d/` populated. | ✅ |
| 2026-04-16 | Shell prompt migrated: p10k removed, Starship 1.24.2 installed. Ghostty configured: MesloLGS Nerd Font Mono 14.5pt, Catppuccin Mocha theme, 0.92 opacity, 10/8 padding. OrbStack installed (replaces Docker Desktop). | ✅ |
| 2026-04-16 | Tailscale DNS+routing workaround: `tailscale set --accept-routes=true`; manual route `10.10.0.0/16 via 100.64.0.3` added (not persistent); `/etc/resolver/home.timmcg.net` created (persistent). `home.timmcg.net` resolves correctly. Root issue: brew daemon lacks Network Extension. | ⚠️ |
| 2026-04-16 | Claude Code config parity with tesla: `CLAUDE.md` synced from AIKB, `statusline-command.sh` copied, `settings.json` updated with Stop hook + statusLine. | ✅ |
| 2026-04-19 | Diagnosed and fixed Runway app crash on macOS Tahoe. Root cause 1: `~/.gemini/telemetry.json` had grown to 2.8 GB — `fs.readFileSync` on startup exhausted Node.js heap → `EXC_BREAKPOINT`. Fixed by tail-reading (512 KB) + auto-trim at 50 MB threshold in Runway. Root cause 2: packaged app was built with Electron 34 while node_modules had 35.7.5; npm workspaces hoisting prevented electron-builder from seeing the module without a pinned version. Both fixes shipped in `mcglothi/runway` commit `22708fc`/`516e13f`. | ✅ |
| 2026-04-19 | Installed `coreutils` via Homebrew to provide `gtimeout` — required by `aikb-session-stop.sh` (was hardcoded to `/usr/bin/timeout` which doesn't exist on macOS). Stop hook now fully functional: closeout, build_candidates, release-session, and git push all run on session end. | ✅ |
| 2026-04-19 | Set up nightly AI log rotation via launchd. `_tools/maintenance/ai-log-cleanup.sh` trims Gemini telemetry, Gemini/Codex/Claude session files, Codex TUI log, and Codex SQLite log on a retention schedule. Runs at 03:15 daily via `com.mcglothi.ai-log-cleanup.plist`. | ✅ |
| 2026-04-17 | Added QNAP QNA-UC10G1SF (USB4 SFP+) for 10G to USW-Aggregation port 5. Finisar FTLX8574D3BCV SR modules both ends. Link dead — Apple Aquantia driver on macOS Tahoe has no optical SFP+ support (copper-only IOMediumDictionary, no `10Gbase-SR`). No software fix without disabling SIP. Need Sonnet Solo 10G SFP+ (`SOLO10G-SFP-T3`) to replace adapter. | ⚠️ |
| 2026-04-17 | Display setup: Philips SWL9753S/37 USB-C→DP1.4 dongle → Dark Matter 43305 DP-2. Confirmed 5120x1440@120Hz native. Input Leap 3.0.3 installed (server on feynman as systemd user service, client on newton via launchd). SSL certs generated and fingerprints exchanged. Monitor switching via DDC: feynman uses ddcutil setvcp, newton uses m1ddc display 2. Toggle server running on feynman:7474 (Flask, systemd). Hammerspoon installed, Cmd+Alt+Ctrl+F1 → switch to feynman. KDE Meta+F9 → switch to newton (needs re-login). | ✅ |
| 2026-04-16 | Tailscale route re-verified after session gap — route was still in place (`sudo route add -net 10.10.0.0/16 100.64.0.3` returned "File exists"). Tesla reachable at `10.10.190.57`. Note: direct Tailscale peer IP `100.64.0.4` times out (expected with brew daemon); always use home IP via subnet route instead. If route drops after reboot/sleep: `sudo route add -net 10.10.0.0/16 100.64.0.3` | ✅ |
| 2026-04-16 | Dev tools installed (brew): `uv` 0.11.7, `fd` 10.4.2, `tree`, `wget`, `ripgrep` 15.1.0, `jq`, `awscli` 2.34.30, `ansible` core 2.20.4. Note: `fd` alias from `common-aliases` plugin resolves correctly on next shell open. | ✅ |
| 2026-04-16 | AI CLIs installed: Gemini CLI 0.38.1 (npm), Codex CLI 0.121.0 (npm), OpenCode 1.4.6 (npm). Casks: Cursor 3.1.15, Claude Desktop 1.2773.0, ChatGPT Desktop 1.2026.051. | ✅ |
| 2026-04-16 | Agent configs installed: `~/.gemini/GEMINI.md` + `settings.json` (MCP + stop hook), `~/.codex/AGENTS.md` + `config.toml` + agents dir (orchestrator/researcher/reviewer/worker — paths fixed for macOS), `~/.config/opencode/opencode.json` (aikb-search MCP enabled). `~/.claude/settings.local.json` copied from tesla (pre-approved Bash permissions). | ✅ |
| 2026-04-16 | Repos cloned to `~/code/`: ai-hub, kyloch, opensoak, ansible, laptime, scripts, cliparr, timmcg-landing, ai-knowledge-base, aikb-bootstrap. | ✅ |
| 2026-04-16 | aikb-search venv built, 927 chunks indexed across 128 files, git post-commit hook installed, MCP registered with Claude Code. | ✅ |

---

## Machine Specs

| Item | Value |
|------|-------|
| OS | macOS 26.4.1 (Tahoe) |
| Kernel | Darwin 25.4.0 |
| Model | MacBook Pro (M5 Max) |
| Chip | Apple M5 Max |
| Memory | 128 GB |
| Storage | 3.6 TB SSD |
| Hostname | newton |
| Architecture | arm64 (Apple Silicon) |
| Tailscale IP | 100.64.0.5 |

---

## Environment Profile

| Variable | Value |
|----------|-------|
| Home directory | `/Users/mcglothi/` |
| Code root | `~/code/` |
| Package manager | `brew` (Homebrew at `/opt/homebrew`) |
| Init system | `launchd` |
| Python command | `python3` |
| Shell | `zsh` |
| Architecture | `arm64` |

---

## Tool Versions
| Tool | Version | Notes |
|------|---------|-------|
| Tailscale | 1.96.4 | Homebrew; daemon as system LaunchDaemon; headscale `hs.timmcg.net` |
| gh CLI | 2.89.0 | Homebrew; authenticated as `mcglothi` |
| Node.js | 25.9.0 | Homebrew |
| Bitwarden CLI | 2.x | Homebrew; pointing to `vault.home.timmcg.net` |
| Git | Apple Git | System |
| Starship | 1.24.2 | Brew; replaces p10k; config `~/.config/starship.toml`; Catppuccin Mocha colors |
| OrbStack | latest | Cask; replaces Docker Desktop |
| MesloLGS Nerd Font | latest | Cask; used by Starship + Ghostty |
| uv | 0.11.7 | Brew; Python package/project manager |
| fd | 10.4.2 | Brew; fast `find` replacement |
| ripgrep | 15.1.0 | Brew; `rg` command |
| tree | latest | Brew |
| wget | latest | Brew |
| jq | latest | Brew |
| awscli | 2.34.30 | Brew |
| ansible | core 2.20.4 | Brew |
| wakeonlan | 0.42 | Brew; installed 2026-04-22 and verified waking Feynman via 10G MAC |
| Gemini CLI | 0.38.1 | npm global |
| Codex CLI | 0.121.0 | npm global |
| OpenCode | 1.4.6 | npm global |
| Cursor | 3.1.15 | Cask |
| Claude Desktop | 1.2773.0 | Cask |
| ChatGPT Desktop | 1.2026.051 | Cask |

---

## SSH Keys Present
| Key | Purpose |
|-----|---------|
| `~/.ssh/id_rsa` | Personal GitHub + general hosts |
| `~/.ssh/svc_claude` | `svc_claude` account on lab servers |
| `~/.ssh/svc_gemini` | `svc_gemini` account on lab servers |
| `~/.ssh/svc_codex` | `svc_codex` account on lab servers |
| `~/.ssh/svc_ansible` | `svc_ansible` account for Ansible runs |

---

## Tailscale Notes
- **App version:** Standalone Tailscale.app (v1.96.5, NOT App Store version).
- **Headscale:** Connected to `https://hs.timmcg.net`, registered on user `tim` as `newton` (100.64.0.6).
- **DNS/Subnet Routing:** `--accept-routes` and `--accept-dns` enabled. Split-DNS handles `home.timmcg.net` via `10.10.0.2`.
- **Legacy cleanup:** Homebrew daemon (`com.tailscale.tailscaled.plist`) removed and formula uninstalled 2026-04-20.

## KVM / Desk Setup

**Physical:** newton on laptop arm next to feynman. Shared: Dark Matter 43305 49" ultrawide (5120x1440@120Hz). 

**Newton Lab Dock (OWC Thunderbolt 5 Hub):**
- **Upstream:** Single Thunderbolt 5 cable providing **140W** power delivery to Newton.
- **Downstream 1:** Sonnet Solo 10G SFP+ Adapter (10G Fiber to Lab Agg Switch).
- **Downstream 2:** Philips SWL9753S/37 USB-C→DP1.4 dongle to monitor DP-2 (confirmed 5120x1440@120Hz).
- **Downstream 3:** Available for expansion.
- **Status:** Hardware purchased 2026-04-21; pending delivery and final integration.

**Input sharing:** Input Leap 3.0.3. feynman = server (keyboard/mouse), newton = client. newton is RIGHT of feynman in layout. Config: `~/.config/input-leap/input-leap.conf` (feynman), client autostart via launchd plist on newton.

**Monitor switching:** DDC/CI via toggle server on feynman port 7474.
- feynman→newton: `Meta+F9` (KDE, needs re-login) or `~/bin/monitor-to-newton.sh`
- newton→feynman: `Cmd+Alt+Ctrl+F1` (Hammerspoon) or `~/bin/monitor-to-feynman.sh`
- Direct toggle: `curl http://10.10.145.26:7474/toggle`
- Status: `curl http://10.10.145.26:7474/status`
- DDC values: feynman=DP-1 (input 7), newton=DP-2 (input 8), I2C bus 6

**ESP32 button (TODO):** Hit `http://10.10.145.26:7474/toggle`. If response has `action_required: newton`, also hit newton's local switch endpoint. Firmware = ~30 lines MicroPython.

---

## 10G Networking — Status & Notes

| Interface | Device | Status | Notes |
|-----------|--------|--------|-------|
| `en8` | **Sonnet Solo 10G SFP+** (`SOLO10G-SFP-T3`) | ✅ Active | Linked at 10G via OWC TB5 Hub and HiFiber `SFP-10G-SR` optics. |
| — | HiFiber SFP-10G-SR | Installed | 10G SR, 850nm, MMF. Confirmed 0% loss to gateway. |
| — | Ubiquiti USW-Aggregation port 5 | Linked | Successfully negotiating 10Gbps. |
| `en7` | QNAP QNA-UC10G1SF | 🛑 Deprecated | Optical SFP+ not supported on macOS Tahoe; retired in favor of Sonnet. |

**Strategy:** Newton Lab Dock (OWC TB5) serves as the primary backbone. The Sonnet adapter provides a dedicated 10G fiber lane to the homelab backbone, ensuring Newton remains a "Primary Agent Orchestrator" with high-bandwidth access to Hopper and Babbage.

Static IP strategy simplified: **DHCP with UDM Reservation**.
- `en8` (Sonnet 10G) set to DHCP on macOS.
- Manual static management retired to prevent DNS resolution conflicts.
- Remote access preference: Tailscale MagicDNS (`newton` -> `100.64.0.6`).

---

## Not Yet Installed
- **🧪 Hermes local test on newton** — validate whether Hermes is worth keeping as a native Newton lane and document the install/runtime path if it is
- **⚠️ KDE Meta+F9 shortcut** — khotkeys entry written, needs feynman re-login to activate
- Local LLM tooling (Ollama, LM Studio, MLX) — do when home
- Apps: Discord, Google Messages, Plex Media Player, Fantastical, ~~Hammerspoon~~ ✅ 2026-04-17, Tor Browser
- Agent auth: Gemini CLI (`gemini auth login`), Codex CLI auth, Bitwarden (`bwu`)
- AWS config (`~/.aws/`) — copy credentials or `aws configure`
- ~~Repos cloned~~ ✅ 2026-04-16 (ai-hub, kyloch, opensoak, ansible, laptime, scripts, cliparr, timmcg-landing, ai-knowledge-base, aikb-bootstrap)
- ~~Claude Code stop hook~~ ✅ configured 2026-04-16
- ~~AWS CLI~~ ✅ installed 2026-04-16
- ~~Ansible~~ ✅ installed 2026-04-16
- ~~`uv`~~ ✅ installed 2026-04-16
- ~~Gemini CLI~~ ✅ installed 2026-04-16
- ~~Codex CLI~~ ✅ installed 2026-04-16
- ~~Cursor~~ ✅ installed 2026-04-16
- ~~`tree`, `wget`, `fd`, `ripgrep`, `jq`~~ ✅ installed 2026-04-16
- ~~Claude Desktop~~ ✅ installed 2026-04-16
- ~~ChatGPT Desktop~~ ✅ installed 2026-04-16
- ~~Sonnet Solo 10G SFP+~~ ✅ 2026-04-21 (purchased)

## Not Installed (cross-machine hazards)
Do not assume these exist on this machine:
- `pacman` / `yay` — use `brew`
- `systemctl` — use `launchctl` or `brew services`
- `/home/` paths — home is `/Users/mcglothi/`
- `lms` (LM Studio CLI) — not yet installed

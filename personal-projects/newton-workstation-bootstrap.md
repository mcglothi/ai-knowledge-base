---
tags: [newton, macbook-pro, bootstrap, workstation, apple-silicon, local-llm, ollama, llama.cpp, mlx, brew]
last_updated: 2026-04-22
---

# Newton Workstation Bootstrap
**Last Updated:** 2026-04-22
**Summary:** Planning document for the new MacBook Pro (`Newton`) arriving on 2026-04-16. Tracks the workstation welcome package, bootstrap targets, and Tesla rehearsal work so the eventual deployment can be scripted cleanly.

## Goals
- Make `Newton` productive as a primary workstation within the first setup session.
- Prefer idempotent bootstrap steps that can be rerun safely.
- Rehearse new apps and tooling on `tesla` before locking the Newton baseline.
- Treat local-model performance as a first-class requirement, not an afterthought.
- 2026-04-16 follow-up: Newton setup exposed enough AIKB/bootstrap repetition that the repo now needs a dedicated "new machine onboarding" workflow, not just the first-time installer.

## Bootstrap Layers
1. Base machine: Xcode CLT, Homebrew, git, shell, dotfiles, SSH, macOS defaults.
2. Developer tooling: VS Code, Cursor, AI CLIs, Docker/OrbStack, cloud/ops CLIs, terminals.
3. Personal workstation layer: browsers, communication apps, media apps, launch items, login/account checklist.
4. Local AI stack: local model runtimes, benchmark harness, model cache/layout, service startup policy.

## Power & Lock Configuration (Newton Travel Mode)
- **Lid Sleep:** Disabled to allow travel between offices without interrupting tasks.
  - Command: `sudo pmset -a disablesleep 1`
- **Password Lock:** Set to 1-hour delay after display sleep.
  - Command: `defaults write com.apple.screensaver askForPassword -int 1`
  - Command: `defaults write com.apple.screensaver askForPasswordDelay -int 3600`

## Target Software Set

### Core developer / AI
- Homebrew
- git
- GitHub CLI
- Node.js / npm
- Python / `uv` / `pipx`
- Codex CLI
- Gemini CLI
- Claude Code
- Bitwarden CLI
- AWS CLI
- Ansible
- Docker Desktop or OrbStack
- VS Code
- Cursor

### Browsers
- Brave
- Google Chrome
- Firefox
- Tor Browser

### Communication / daily-use
- [x] MacWhisper (Settings mirrored from tesla 2026-04-16)
  - **Permissions Required:**
    - Accessibility (for global shortcuts/dictation)
    - Microphone (for direct recording)
    - Screen & System Audio Recording (for meeting transcription)
    - Full Disk Access (optional, recommended for drag-and-drop)
- [ ] Discord
- [ ] Telegram Desktop
- Spotify
- Google Messages
- Signal Desktop
- Plex Media Player
- Fantastical (evaluation)

### Terminals / utilities
- iTerm2
- Ghostty
- WezTerm
- Hammerspoon (for automation and networking state)
- ripgrep
- fd
- jq
- tree
- wget
- Tailscale GUI app

## Networking Strategy & State Detection
- **Wi-Fi (Primary Name):** standard DHCP for `newton.home.timmcg.net`.
- **10Gb Thunderbolt (High Traffic):** Static IP `10.10.110.110` mapped to `newton10g`. Use this for heavy lab traffic (Hopper/Babbage).
- **2026-04-24 Sonnet/OWC status:** Replacement HiFiber `SFP-10G-SR` transceivers arrived and were installed. `en8` links at `10Gbase-T <full-duplex,flow-control>` automatically. Pings to gateway `10.10.0.1` and lab hosts (Hopper) are stable (<0.3ms). Newton is now live on the 10G backbone.
- **WiFi (Mobile):** Standard roaming DHCP.
- **State Assessment:** To check if Newton is docked and capable of heavy local-LLM loads or workstation syncs, ping the 10Gb static IP.
- **Automated Reporting:** Evaluate a low-power **Hammerspoon** script to detect 10Gb link changes and update `_state.yaml` in AIKB.
  - *Battery Caution:* Ensure Hammerspoon triggers are event-driven (link change) rather than polling to minimize background power draw.

## Local Model Runtime Direction
- Primary local API/runtime: `LM Studio` (via `lms` CLI)
- Apple-native experimentation path: `MLX` / `mlx-lm`
- Secondary/Experimental: `Ollama` (manual start only)

## Tesla Rehearsal Notes
- 2026-03-29: Installed `Fantastical` on `tesla` via Homebrew cask for evaluation ahead of Newton rollout.
- 2026-03-29: Installed `Alacritty` briefly on `tesla`, but macOS Gatekeeper blocked launch with an Apple malware-verification warning. Removed it and switched the terminal evaluation set to `Ghostty` and `WezTerm`.
- 2026-03-29: Added matching starter configs for `Ghostty` and `WezTerm` on `tesla` so the terminal comparison is based on tuned defaults rather than stock appearance. Current shared direction: `MesloLGS NF`, `Catppuccin Mocha`, 14.5 pt font size, padded layout, and subtle translucency.
- 2026-03-29: Confirmed Firefox already existed on `tesla` as a standalone app bundle, so Homebrew cask install failed due to existing `/Applications/Firefox.app`. On a clean Newton install, Firefox should be managed by Homebrew from the start.
- `tesla` remains the proving ground for new terminal, calendar, browser, and local-model tooling before finalizing the Newton baseline.

## Open Questions Before Script Freeze
- Choose primary container UX: Docker Desktop vs OrbStack.
- Decide whether Ghostty, iTerm2, or WezTerm becomes the preferred macOS terminal.
- Define the first benchmark matrix for Newton across `Ollama`, `llama.cpp`, and `MLX`.
- Decide which apps should auto-start on login versus remain manual.
- Capture browser extension and account/login manifests for deterministic restore.

## Next Implementation Steps
1. Convert this plan into a `Brewfile` plus a small bootstrap shell entrypoint.
2. Separate fully automatable steps from guided manual steps (Tailscale auth, Bitwarden unlock, app sign-ins, permissions).
3. Rehearse chosen apps and settings on `tesla` during the two weeks before Newton arrives.
4. Add a Newton-specific postflight checklist for local-model benchmarking, login setup, and account pairing.

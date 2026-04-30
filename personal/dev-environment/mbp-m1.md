# Dev Environment: mbp-m1
**Last Updated:** 2026-04-22
**Summary:** MacBook Pro M1 13" (Apple Silicon). Hostname: `tesla`. macOS Sequoia. Canonical content file retained for backward compatibility; hostname alias entrypoint lives at [`tesla.md`](tesla.md).

---

## Maintenance Log
| Date | Action | Status |
|------|--------|--------|
| 2026-04-12 | Fixed Oh My Zsh `powerlevel10k` theme not found error by symlinking `~/.powerlevel10k` into `~/.oh-my-zsh/custom/themes/`. Cleaned up redundant manual theme sourcing and plugin installation reminders from `~/.zshrc`. | ✅ |
| 2026-04-12 | Reconfigured `Ghostty` and `WezTerm` to match the current `iTerm2` baseline on tesla. Updated both to use `MesloLGS NF` at 22 pt, a customized `Dracula` theme with a darker `#1e1f29` background, and 85% opacity with blur. This overrides the previous 14.5 pt Catppuccin "shared direction" to maintain visual consistency across all terminal clients during the transition. | ✅ |
| 2026-04-12 | Evaluated MacWhisper and custom `whisper-cpp` CLI bridge (`vcmd`) for voice-to-terminal commands on tesla. Determined that native macOS Dictation (Hold `Command`) is superior for low-latency terminal usage on Apple Silicon. Installed `MacWhisper.app` via brew cask as a long-form transcription fallback. Cleaned up experimental `whisper-cpp`, `sox`, and local models to reclaim disk space. | ✅ |
| 2026-04-10 | Established strict account accountability rules in `AGENTS.md`. Deployed `svc_gemini`, `svc_claude`, and `svc_codex` user accounts to `turing` and `babbage` with individual authorized keys. Generated a dedicated `svc_ansible` SSH key on tesla, pushed to Vaultwarden, and authorized it on servers. Updated `ansible/ai/inventory.ini` to use `svc_ansible` account and key properly. | ✅ |
| 2026-03-29 | Added polished starter configs for `Ghostty` and `WezTerm` on tesla to compare terminal candidates ahead of Newton arrival. Ghostty config lives at `~/Library/Application Support/com.mitchellh.ghostty/config.ghostty`; WezTerm config lives at `~/.wezterm.lua`. Both use `MesloLGS NF`, `Catppuccin Mocha`, 14.5 pt text, transparent/glassy dark backgrounds, comfortable padding, and macOS-friendly window behavior. | ✅ |
| 2026-03-29 | Replaced `Alacritty` with `Ghostty` and `WezTerm` on tesla after macOS Gatekeeper blocked `Alacritty` with "Apple could not verify it was free of malware." Installed both via Homebrew cask (`brew install --cask ghostty wezterm`) and verified app bundles at `/Applications/Ghostty.app` and `/Applications/WezTerm.app`. This is now the active terminal evaluation set for Newton planning, while `iTerm2` remains the known-good baseline. | ✅ |
| 2026-03-29 | Installed `Alacritty` and `Fantastical` via Homebrew cask on tesla as part of the Newton workstation-bootstrap rehearsal. `alacritty` installed successfully but Homebrew marks the cask deprecated because it does not pass macOS Gatekeeper checks; keep it as an evaluation candidate, not the sole terminal standard yet. Verified app bundles at `/Applications/Alacritty.app` and `/Applications/Fantastical.app`. Firefox was already present at `/Applications/Firefox.app` (`kMDItemVersion` `147.0.4`); `brew install --cask firefox` failed because the existing app bundle was not Homebrew-managed, so leave Firefox in place on tesla and let the future Newton bootstrap install it cleanly on a fresh machine. | ✅ |
| 2026-03-21 | Installed Tor Browser via Homebrew cask (`brew install --cask tor-browser`) on tesla for privacy-focused browsing and onion-site re-orientation. Verified app bundle at `/Applications/Tor Browser.app` with `CFBundleShortVersionString` `15.0.7`. | ✅ |
| 2026-03-21 | Installed uncensored local models `qwen35-uncensored-9b:q6` and `llama31-fei-uncensored-8b:q5km` from Hugging Face GGUFs via local Ollama Modelfiles in `~/Models/modelfiles/`. The Qwen build uses `HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive-Q6_K.gguf` (6.9 GB) and the Llama build uses `MaziyarPanahi/Llama-3.1-8B-Instruct-Fei-v1-Uncensored.Q5_K_M.gguf` (5.3 GB). Had to update Ollama from `0.11.8` to `0.18.2` using the cached app bundle because the older runtime could not load GGUF architecture `qwen35` (`unknown model architecture: 'qwen35'`). Both models are now registered locally in Ollama on tesla; the Qwen model is more reasoning-style and may emit `<think>` tags, while the Llama model is intended as a cleaner A/B comparison. | ✅ |
| 2026-03-21 | Raised Apple Silicon GPU wired-memory limit for local LLM workloads by setting `iogpu.wired_limit_mb=13312` (~13 GB) on tesla. Verified the live sysctl and Metal `recommendedMaxWorkingSetSize` both report `13312` MB. Installed persistent boot-time LaunchDaemon at `/Library/LaunchDaemons/com.timmcg.iogpu-wired-limit.plist`; source plist stored at `~/code/scripts/com.timmcg.iogpu-wired-limit.plist`. Chosen as the practical top-end on this 16 GB M1 because it improves on the default ~12 GB limit while still leaving ~3 GB for macOS. | ✅ |
| 2026-03-21 | Cloned `jeffhammond/STREAM`, installed Homebrew `libomp`, and ran STREAM on Apple M1. Best observed rates with `STREAM_ARRAY_SIZE=40000000`, `NTIMES=20`: single-thread `Copy 59635 MB/s`, `Scale 59041 MB/s`, `Add 57443 MB/s`, `Triad 57296 MB/s`. OpenMP with 4 threads was roughly similar/slightly slower; 8 threads was materially slower on this machine. | ✅ |
| 2026-03-09 | Migrated to Tailscale GUI app (`tailscale-app`). Configured with `hs.timmcg.net`, registered on headscale server, and renamed node to `tesla` (100.64.0.4). | ✅ |
| 2026-03-07 | Integrated `phi4:14b` for reasoning and created `local-compact.sh` for session state compaction. Updated AI Hub to support Ollama provider. | ✅ |
| 2026-03-05 | Configured MCP servers (github-aikb, chrome-devtools, playwright, fetch, multicli) for both `gemini` and `codex` CLIs. Copied Codex agent profiles from feynman. | ✅ |
| 2026-03-03 | Fixed AI Hub UI bug where empty state always said "Ask Claude". Now dynamically updates per provider. Deployed via TrueNAS jump host. | ✅ |
| 2026-03-03 | Missing Tailscale menubar icon on tesla. Identified that Homebrew CLI version is installed without GUI. To fix: `sudo brew services stop tailscale` and `brew install --cask tailscale-app`. Server: `https://hs.timmcg.net`. | ✅ |
| 2026-03-03 | Fixed AI Hub UI bug where empty state always said "Ask Claude". Now dynamically updates per provider. Deployed via TrueNAS jump host. | ✅ |
| 2026-02-27 | Darkened homelab homepage (www.home.timmcg.net) background with subtle radial gradient and enhanced scanlines to match timmcg.net landing page. | ✅ |
| 2026-02-26 | Installed local LLM tooling: LM Studio 0.4.5 (brew cask), Open WebUI 0.8.5 (python3.11 venv, LaunchAgent on :8080), Continue.dev config for Cursor. Models: qwen2.5:7b, llama3.1:8b via Ollama. | ✅ |
| 2026-02-26 | Updated homelab homepage weather location to Topsham, ME (04086). | ✅ |
| 2026-02-26 | Improved homelab homepage aesthetic (www.home.timmcg.net) with darker background and higher contrast green text for better readability. | ✅ |
| 2026-02-26 | Fixed Homebrew ownership (`sudo chown -R $USER /opt/homebrew`) following UID change (502 -> 1000). Updated `~/.zshrc` to use `eval "$(/opt/homebrew/bin/brew shellenv)"` for correct PATH precedence. Upgraded `gemini-cli` to `0.30.0`. | ✅ |
| 2026-02-24 | Changed UID from 502 to 1000. Fixed file ownership issues in `~/Library` using `sudo chown -R`. Required granting Full Disk Access to iTerm2 to bypass SIP/TCC restrictions. Menu bar items (Clock, etc.) were missing; visibility flags injected into `com.apple.controlcenter`. | ⚠️ IN PROGRESS — Logout/Reboot required to clear process caches. |

---

## Machine Specs

| Item | Value |
|------|-------|
| OS | macOS 15.6.1 (Sequoia) |
| Model | MacBook Pro 13" (M1) |
| Hostname | tesla |
| Architecture | arm64 (Apple Silicon) |

---

## Environment Profile

| Variable | Value |
|----------|-------|
| Home directory | `/Users/mcglothi/` |
| Code root | `~/code/` |
| Package manager | `brew` (Homebrew) |
| Init system | `launchd` |
| Python command | `python3` (3.9.6 system) / `python3.11` (for AWS env) |
| Shell | `zsh` |
| Architecture | `arm64` |

---

## Tool Versions
| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.9.6 (System) / 3.11.9 (AWS CLI) / 3.12.3 (brew default) | |
| Ollama | 0.18.2 | Running as background service on :11434 |
| Open WebUI | 0.8.5 | Python3.11 venv at `~/code/.venvs/open-webui`; LaunchAgent on :8080; data at `~/.local/share/open-webui` |
| LM Studio | 0.4.5 | /Applications/LM Studio.app; local server on :1234 when running |
| Git | 2.39.5 (Apple Git-154) | |
| Node.js | v24.11.1 | |
| Homebrew | 5.0.14 | |
| AWS CLI | 2.16.3 | |
| Bitwarden CLI | 2026.1.0 | Configured to `vault.home.timmcg.net` |
| Ghostty | v1.3.1 | Homebrew cask; matched to iTerm2 baseline (Dracula, 22pt) |
| WezTerm | `20240203-110809` | Homebrew cask; matched to iTerm2 baseline (Dracula, 22pt) |

---

## Installed Tools (notable)
- `brew` (Homebrew) — primary package manager
- `libomp` — v22.1.1 via Homebrew; needed for OpenMP builds with Apple clang
- `node` / `npm` — v24.11.1
- `aws` CLI — v2.16.3
- `bw` (Bitwarden CLI) — v2026.1.0 (pointing to local Vaultwarden)
- `wakeonlan` — workstation baseline tool for waking Feynman; install with `brew install wakeonlan` if missing
- `bwu` — shell function in `~/.zshrc`; unlocks vault and writes session to `~/.bw_session`
- `local-compact.sh` — `~/code/scripts/local-compact.sh`; uses Ollama/phi4 to summarize AI session state
- `ollama` — v0.18.2; models at `~/.ollama/models`; pulled: qwen2.5:7b, llama3.1:8b, phi4:14b, qwen35-uncensored-9b:q6, llama31-fei-uncensored-8b:q5km
- `open-webui` — v0.8.5; venv at `~/code/.venvs/open-webui`; config: `~/Library/LaunchAgents/net.timmcg.open-webui.plist`
- `LM Studio` — v0.4.5; /Applications/LM Studio.app (GUI model browser + OpenAI-compatible server)
- `Ghostty` — v1.3.1 via Homebrew cask; matched to iTerm2 baseline (Dracula, 22pt)
- `WezTerm` — `20240203-110809,5046fc22` via Homebrew cask; matched to iTerm2 baseline (Dracula, 22pt)
- `Fantastical` — v4.1.10 via Homebrew cask; calendar client evaluation on macOS
- Continue.dev — Cursor extension; config at `~/.continue/config.json`; uses Ollama backend

## Local LLM Services

| Service | Port | Auto-start | Notes |
|---------|------|------------|-------|
| Ollama | 11434 | Yes (system) | `ollama serve`; OpenAI-compatible at `/v1` |
| Open WebUI | 8080 | Yes (LaunchAgent) | UI at http://localhost:8080 |
| LM Studio | 1234 | Manual | Start from app; OpenAI-compatible server |

## Local LLM Models (Ollama)
| Model | Size | Best for |
|-------|------|----------|
| qwen2.5:7b | 4.7GB | General / code |
| llama3.1:8b | 4.9GB | Chat / reasoning |
| qwen2.5-coder:7b | 4.4GB | Code specifically (recommended pull) |
| phi4:14b | 9.1GB | Reasoning / summarization (used by `local-compact.sh`) |
| qwen35-uncensored-9b:q6 | 7.4GB | Uncensored experimentation / direct testing |
| llama31-fei-uncensored-8b:q5km | 5.7GB | Uncensored comparison model with more conventional Llama chat behavior |

## Diagnostic Heuristics & Machine Quirks

- **UID Drift (502 -> 1000):** A major system migration in Feb 2026 changed the primary user UID. If Homebrew or `~/Library` files report permission errors, check ownership with `ls -aln`. Fixed with `sudo chown -R $USER`.
- **Tailscale Split-Personality:** Both the Homebrew CLI (`tailscale`) and the macOS GUI app (`tailscale-app`) can be present. The GUI app is required for the menu bar icon and easier headscale integration. If the icon is missing, verify if only the CLI version is active via `brew services list`. 
- **Alacritty on macOS:** Homebrew currently deprecates the cask because it fails Gatekeeper verification, and macOS may block launch with a malware-verification warning. Prefer `iTerm2`, `Ghostty`, or `WezTerm` on this machine.
- **Service Verification:** `brew services list` is often flaky on Sequoia. If it reports an error or "stopped" but the service is expected to be up, verify with `pgrep -af <service_name>` and `ps -wwfp <pid>`.

## Not Installed (cross-machine hazards)
Do not assume these exist on this machine:
- `pacman` / `yay` — use `brew`
- `systemctl` — use `launchctl` or `brew services`
- `/home/` paths — home is `/Users/mcglothi/`
- `Tesseract` — install with `brew install tesseract` if needed
- `OpenRGB` — N/A (no addressable RGB hardware)
- `pw-link` / PipeWire — macOS uses CoreAudio
- `reflector` — Arch-specific, not applicable
- `visudo` / `/etc/sudoers.d/` — different permission model on macOS

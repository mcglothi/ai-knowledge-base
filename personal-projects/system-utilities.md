---
context: personal
tags: [scripts, bash, python, feynman, auto-update, btrfs, pacman, vpn, bitwarden, bw, arch, snapshots, dotfiles, rgb]
hosts: [feynman, any-linux]
last_updated: 2026-04-21
---

# System Utilities
**Last Updated:** 2026-04-21
**Summary:** Custom bash and python scripts for system maintenance and automation. Most scripts are feynman-specific; scope is noted per script.

## Environment Requirements
Varies per script — see scope notes below. Most scripts require:
- **[feynman]** `pacman`, `systemd`, `OpenRGB`, `PipeWire`, Btrfs snapshots
- **[any Linux]** `python3`, `bash`
- **[all]** `bw` (Bitwarden CLI via npm) — if installed on the machine

## Repositories
- **Scripts:** [mcglothi/scripts](https://github.com/mcglothi/scripts)
- **Dotfiles:** [mcglothi/dotfiles](https://github.com/mcglothi/dotfiles)

## Scripts

### Auto Update `[feynman]`
`~/code/scripts/auto-update.sh`
- **NVIDIA legacy state (2026-04-21):** feynman has a GTX 1080 Ti (Pascal). Arch/NVIDIA driver support moved Pascal cards off the main 590+ packages; feynman now uses AUR `nvidia-580xx-dkms`, `nvidia-580xx-utils`, `lib32-nvidia-580xx-utils`, plus matching 580xx OpenCL packages.
- **Pacman pins:** `/etc/pacman.conf` pins `nvidia-580xx-dkms`, `nvidia-580xx-utils`, and `lib32-nvidia-580xx-utils`. A backup from the migration exists at `/etc/pacman.conf.bak-codex-nvidia-580xx-20260421`.
- **Script behavior:** The update script hard-stops if `nvidia-550xx-dkms` is installed, requires 580xx pins when `nvidia-580xx-dkms` is installed, and verifies `nvidia.ko` DKMS modules for `linux-lts`, `linux`, and `linux-zen` after upgrades. `linux-lts` is treated as the protected fallback and missing LTS NVIDIA modules are fatal.
- **2026-04-21 update notes:** Official pacman update completed after removing obsolete `ebtables` and old Plasma 5 `kio5-extras`/`kdsoap-qt5`. NVIDIA 580.142 modules built successfully for `linux-lts 6.18.23-1`, `linux 6.19.12.arch1-1`, and `linux-zen 6.19.12.zen1-1`. Reboot is required before `nvidia-smi` works again because the running kernel still has the pre-upgrade NVIDIA module loaded while userland is now 580.142.

### KDE Window Management `[feynman]`
 \`[feynman]\`
- **Current Strategy:** Master startup script (\`~/code/scripts/launch-desktop.sh\`) using \`kdotool\` (v0.2.2) and \`qdbus\`.
  - **Correction (2026-02-27):** Programmatic desktop movement now uses \`kdotool set_desktop_for_window "$id" "$num"\` (1-indexed) as \`qdbus setWindowOnDesktop\` is not available in Plasma 6.
- **Challenges:**
  - **Wayland/NVIDIA Stability:** Electron apps (VacuumTube) and Firefox often crash when programmatically moved before initial paint.
  - **VacuumTube updater prompt (fixed 2026-04-21):** Shutdown authentication popup mentioning a `.deb` package was traced to VacuumTube's Electron auto-updater. `launch-desktop.sh` starts `~/.local/bin/vacuumtube`, and the app logged `Found package-type: deb` before shutdown. VacuumTube branch `codex/disable-linux-updater` now skips `autoUpdater.checkForUpdatesAndNotify()` on Linux and the rebuilt `dist/linux-unpacked` launcher no longer emits the updater/deb log.
  - **Class Ambiguity:** Multiple Brave/Konsole windows require distinct apps (Firefox vs Brave) or title-matching to position correctly.
  - **Ghost IDs:** Validation audits can give false positives if checked too soon after a crash.
- **Current Layout (Desktop 1):** Firefox, Konsole, Brave.
- **Current Layout (Desktop 4):** Steam.
- **Current Layout (TV Grid):** Spotify, Jellyfin, Slack (Top); Signal, Google Messages, Discord (Bottom) — all pinned to all desktops.
- **Status:** ✅ RECENTLY UPDATED — Move commands fixed to use kdotool; layout simplified.

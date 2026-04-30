---
context: personal
---
# Dev Environment: feynman (Arch Desktop)
**Last Updated:** 2026-04-22
**Summary:** Primary Linux workstation running Arch Linux with KDE Plasma. x86_64.

---

## Machine Specs

| Item | Value |
|------|-------|
| OS | Arch Linux |
| Desktop | KDE Plasma (Wayland) |
| CPU | 12 Cores (x86_64) |
| RAM | 31 GB |
| GPU | NVIDIA GeForce GTX 1080 Ti |
| Hostname | feynman |
| IP (1G) | `10.10.125.197` |
| IP (10G) | `10.10.145.26` |
| MAC (1G) | `e0:d5:5e:2b:c6:e2` (enp0s31f6) |
| MAC (10G) | `6c:fe:54:1c:61:80` (enp2s0f0np0) |

---

## Environment Profile

| Variable | Value |
|----------|-------|
| Home directory | `/home/mcglothi/` |
| Code root | `~/code/` |
| Package manager | `pacman` (AUR: `yay`) |
| Init system | `systemd` |
| Python command | `python3` |
| Shell | `zsh` |
| Architecture | `x86_64` |

---

## Tool Versions

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.14.2 | |
| Git | 2.52.0 | |
| AWS CLI | 1.44.15 | |
| Tesseract | 5.5.2 | OCR — not on other machines |

---

## Installed Tools (notable)
- `VacuumTube` — installed to `~/.local/bin/vacuumtube` (built from source at `~/code/VacuumTube/dist/linux-unpacked/vacuumtube`)
- `Jellyfin Desktop` — installed natively via AUR (plex-media-player removed)
Tools present here that may not exist on other machines:
- `Tesseract` — OCR engine
- `OpenRGB` — RGB hardware control
- `pw-link` (PipeWire) — audio routing
- `reflector` — Arch mirror refresh
- `expect` — scripted terminal interaction (used by autoVPN.sh)
- `bw` (Bitwarden CLI) — installed via npm
- Btrfs — root filesystem (snapshots in `/.snapshots`)
- NVIDIA proprietary drivers

## AI Tools
- **Claude Code** — configured with `github-aikb` MCP and `aikb-search` MCP (confirmed working 2026-02-23)
- **Gemini CLI** — configured with `github-aikb` MCP and `multicli` MCP (as of 2026-03-05)

## Not Installed (cross-machine hazards)
Do not assume these exist on feynman:
- `brew` / Homebrew — use `pacman` or `yay`
- `launchd` — use `systemctl`
- `/Users/` paths — home is `/home/mcglothi/`

---

## Paths & Configs
- **Code Root:** `~/code/`
- **Dotfiles:** `~/code/dotfiles` (GitHub: `mcglothi/dotfiles`, branch: `master`, SSH remote)
- **APF SSH Key:** `~/tmcglothin-apf-prod.pem`
- **KDE Window Rules:** `~/.config/kwinrulesrc`
  - **"Save my desktop":** Capture and lock current window coordinates (position, size, desktop, monitor).
  - **"Unlock my desktop":** Set window rules to "No Policy" to allow manual movement/resizing.
  - **TV Monitor (Top):** 3x2 Perfect Grid (1280px wide columns), all pinned to all desktops.
  - **Ultrawide (Bottom):** 
    - **Desktop 1:** Firefox, Konsole, Brave.
    - **Desktop 4:** Steam.
  - **Reference:** [`personal-projects/system-utilities.md`](../../personal-projects/system-utilities.md#kde-window-management-feynman)
- **SDDM Config:**
  - **Autologin:** Configured in `/etc/sddm.conf.d/kde_settings.conf` (Session set to `plasma` for KDE 6 Wayland).
  - **Theme:** Custom `hacker` theme in `/usr/share/sddm/themes/hacker/` (based on Catppuccin Mocha).
    - **Aesthetic:** Dark background, hacker green text (`#00ff41`), scanline overlay, and pulsing "ACCESS_" logo.
  - **Display Layout:** Configured in `/usr/share/sddm/scripts/Xsetup` using `xrandr` to align DP-1 (primary) and HDMI-A-2.

## Troubleshooting Notes

- **Shutdown auth prompt / `.deb` package popup (fixed 2026-04-21):** Root cause was VacuumTube's Electron auto-updater running on Linux. KDE autostart launches `~/code/scripts/launch-desktop.sh`, which starts `~/.local/bin/vacuumtube`; logs showed `Found package-type: deb` from VacuumTube/electron-updater before shutdown. Fix applied in `~/code/VacuumTube` branch `codex/disable-linux-updater`: skip `autoUpdater.checkForUpdatesAndNotify()` on Linux, rebuild `dist/linux-unpacked`, and restart VacuumTube. Recent restart logs no longer show `Found package-type: deb` or polkit/auth activity.
- **"Input capture requested" notification (fixed 2026-04-22):** KDE Plasma notification for Wayland input capture portals was triggering toast alerts during monitor/input switching (Input Leap / Deskflow). Fixed by setting `Action=None` for `inputcapturestarted` and `remotedesktopstarted` in `~/.config/xdg-desktop-portal-kde.notifyrc` and setting their values to `0` in `~/.config/knotifyrc`. Applied via `kwriteconfig6` and restarted `plasma-xdg-desktop-portal-kde`.

---

## Wake-on-LAN

**Status:** Configured and persistent (2026-02-27)

| Item | 1G (Onboard) | 10G (Fiber) |
|------|--------------|-------------|
| NIC | `enp0s31f6` | `enp2s0f0np0` |
| MAC | `e0:d5:5e:2b:c6:e2` | `6c:fe:54:1c:61:80` |
| WoL mode | `magic` | `magic` |
| NM connection | `New 802-3-ethernet connection` | `10G Port 0` |

### 10G Fiber Optic
- **NIC:** Intel X710 for 10GbE SFP+ (`i40e`, `enp2s0f0np0`)
- **Switch:** USW-Aggregation port 2, negotiated `10000`
- **Module EEPROM:** `OEM` / `SFP-10G-SR`, LC, 10G Base-SR, 850nm, OM3 length 300m
- **Observed diagnostics (2026-04-22):** TX `-2.21 dBm`, RX `-2.93 dBm`, module temperature `37.26 C`, no alarm/warning flags
- **Comparison note:** Newton is using Finisar `FTLX8574D3BCV` modules on USW-Aggregation port 5 and currently negotiates only 1G, so swapping in the same OEM `SFP-10G-SR` module style used by Feynman is a good next isolation test.

**Remote boot workflow (from Newton, tesla, or any Tailscale-connected machine):**

> **Note:** WoL magic packets are Layer 2 broadcasts and do not traverse Tailscale. Direct broadcast from Newton only works when Newton is **physically on the home LAN**. When remote, always use the TrueNAS relay.

**Primary path — relay via TrueNAS:**

```bash
# Get svc_claude SSH key (requires bwu to have been run)
BW_SESSION=$(cat ~/.bw_session)
# Key is stored at ~/.ssh/svc_claude on Newton

ssh -i ~/.ssh/svc_claude -o StrictHostKeyChecking=no svc_claude@10.10.10.10 "python3 -c \"
import socket
mac='6cfe541c6180'
magic=bytes.fromhex('ff'*6+mac*16)
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
s.sendto(magic,('255.255.255.255',9))
print('Magic packet sent from TrueNAS')
\""
sleep 45
ping -c 3 10.10.145.26
```

**Secondary path — direct broadcast (unreliable from Newton as of 2026-04-28):**

```bash
wakeonlan 6c:fe:54:1c:61:80
ping -c 3 10.10.145.26
ssh 10.10.145.26 "hostname; ip -br addr show enp2s0f0np0"
```

2026-04-22 verification from Newton: Homebrew `wakeonlan` 0.42 sent the packet to Feynman's 10G MAC, after which Feynman answered ping and SSH; Feynman has Arch `wol` 0.7.1 installed at `/usr/bin/wol`.

Fallback path: TrueNAS is always on and on the home LAN, so use it as the WoL relay when the local workstation cannot broadcast.

```bash
# 1. Get svc_claude SSH key from Vaultwarden (requires bwu to have been run)
BW_SESSION=$(cat ~/.bw_session)
bw get password "PAT/SSH/svc_claude" --session "$BW_SESSION" > /tmp/svc_claude_key
chmod 600 /tmp/svc_claude_key

# 2. SSH into TrueNAS (reachable at 10.10.10.10 via Tailscale subnet route)
ssh -i /tmp/svc_claude_key svc_claude@10.10.10.10

# 3. Once on TrueNAS, send the magic packet with Python (`wakeonlan` is not installed there):
python3 -c "
import socket
mac='6cfe541c6180' # Change to e0d55e2bc6e2 for 1G
magic=bytes.fromhex('ff'*6+mac*16)
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
s.sendto(magic,('255.255.255.255',9))
print('Magic packet sent')
"
```

**BIOS:** WoL enabled for both. If boot fails, check UEFI → Power Management.

---

## Open Items

| Item | Notes |
|------|-------|
| ⬜ Split dotfiles/zshrc into shared + machine-specific | Many aliases are feynman-only (pacman, ipmitool, uplayfix, lachlan VPN, broot hardcoded path). Others are cross-machine. Strategy: shared base + per-machine override file sourced at end. |
| ⬜ Move iDRAC password out of zshrc aliases | `racadm` and `serverfans*` aliases have `-P Tinjat1!` in plain text — already on GitHub. Store in Vaultwarden, export via `~/.aikb-env` or a feynman-local override. |
| ✅ Add `nollama` alias to `.zshrc` | `alias nollama='OLLAMA_NOHISTORY=1 ollama'` — already added to tesla. |



## Private Project Repositories
- **ESPhome Configs:** `mcglothi/esphome-configs`
- **Homepage Configs:** `mcglothi/homelab-homepage`
- **Scripts:** `mcglothi/scripts`
- **APF Migration:** `mcglothi/APF`
- **AIKB Bootstrap:** `mcglothi/aikb-bootstrap`

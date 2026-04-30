---
context: personal
---
# Mac Migration Plan

**Last Updated:** 2026-04-23
**Summary:** Steps to migrate AIKB tooling and dev environment from J9RC8S3-LP (W11/WSL2) to a new Mac.
**Status:** Pending — not started

---

## Overview

Current machine: Windows 11 laptop `J9RC8S3-LP`, engineering done inside WSL2 (Ubuntu 24.04).
Target: Mac laptop (hostname TBD). Engineering done natively on macOS. No WSL.

---

## High-Priority Items (AIKB ingest pipeline)

### 1. Outlook Scraper — Replace PowerShell COM with AppleScript

**Current:** `C:\Temp\aikb_outlook_ingest.ps1` — uses `Outlook.Application` COM object via PowerShell
**Mac replacement:** AppleScript via `osascript`

```applescript
-- skeleton
tell application "Microsoft Outlook"
  set theFolder to mail folder "Nutanix Alerts" of default account
  set theMessages to every message of theFolder whose time received > (current date) - 30 * days
  -- extract subject, sender, body, date → write JSON
end tell
```

Action: write `aikb_outlook_ingest.applescript`, wire into shell via `osascript`.

### 2. Windows Task Scheduler → launchd

**Current:** Task `AIKB-Ingest` in Windows Task Scheduler, runs every 4h via XML definition.
**Mac replacement:** `~/Library/LaunchAgents/com.aikb.ingest.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>        <string>com.aikb.ingest</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/YOURUSERNAME/code/AIKB/_tools/ingest/aikb_ingest.sh</string>
    </array>
    <key>StartInterval</key> <integer>14400</integer>  <!-- 4 hours -->
    <key>RunAtLoad</key>     <false/>
    <key>StandardOutPath</key> <string>/tmp/aikb_ingest.log</string>
    <key>StandardErrorPath</key> <string>/tmp/aikb_ingest.log</string>
</dict>
</plist>
```

Load with: `launchctl load ~/Library/LaunchAgents/com.aikb.ingest.plist`

### 3. WSL Paths → Native macOS Paths

| Current (WSL) | Mac replacement |
|---------------|-----------------|
| `/mnt/c/Temp/teams_leveldb` | `~/Library/Containers/MSTeams.../Data/Library/...` (TBD) |
| `/mnt/c/Temp/aikb_last30.json` | `/tmp/aikb_last30.json` |
| `/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe` | `osascript` (AppleScript) |
| `~/code/` | `~/code/` (same — verify on new machine) |

### 4. Teams LevelDB Path on Mac

New Teams 2.0 on Mac also uses Chromium/Electron + IndexedDB. Expected location:

```
~/Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams/EBWebView/
```

Action on new machine: `find ~/Library/Containers -name "*.ldb" 2>/dev/null | head -5` to confirm.
Then update `LDB_PATH` in `teams_ingest.py`.

### 5. Shell Setup

**Current:** zsh in WSL, `~/.zshrc` sources `copilot-wrapper.sh`
**Mac:** zsh is default shell — same dotfile setup should work
- Verify `copilot-wrapper.sh` path references after migration
- Re-source: `echo 'source ~/code/AIKB/_tools/memory-pipeline/copilot-wrapper.sh' >> ~/.zshrc`

### 6. Python Environment

**Current:** `python3.12` via apt, `pip3 install --break-system-packages`
**Mac replacement:** Use Homebrew Python or pyenv — no `--break-system-packages` flag needed

```bash
brew install python@3.12
pip3 install git+https://github.com/cclgroupltd/ccl_chromium_reader.git
```

### 7. Git / GitHub CLI

```bash
brew install git gh
gh auth login
```

### 8. Ansible

```bash
brew install ansible
pip3 install ucsmsdk infoblox_client pyxcli munch bunch pywinrm jmespath
```

---

## Lower Priority Items

| Item | Notes |
|------|-------|
| Bitwarden CLI | `brew install bitwarden-cli` — same `~/.bw_session` pattern |
| SSH keys | Copy `~/.ssh/` or re-generate and add to GitHub + LLBean systems |
| Delinea CLI (`tss`) | Reinstall via Delinea installer on Mac |
| Copilot CLI | `npm install -g @github/copilot-cli` or via gh extension |
| `ansible-builder` / podman | May need Podman Desktop on Mac |

---

## Migration Checklist (run on new machine)

- [ ] Clone AIKB: `git clone git@github.com:tmcglothin_llbean/AIKB.git ~/code/AIKB`
- [ ] Confirm Teams LDB path — update `teams_ingest.py`
- [ ] Write AppleScript Outlook scraper — replace PS script
- [ ] Update `aikb_ingest.sh` — remove PS call, add `osascript` call, fix paths
- [ ] Install launchd plist — update username, load it
- [ ] Run `teams_ingest.py` manually once — verify output
- [ ] Run `outlook_ingest.py` manually once — verify output
- [ ] Run `aikb_ingest.sh` end-to-end — verify git push
- [ ] Update `J9RC8S3-LP.md` → create `<new-hostname>.md`
- [ ] Update `personal/dev-environment/README.md` machine table

---

## Notes

- Windows machine has AIKB ingest working and scheduled — keep running until Mac confirmed working
- Overlap period: both machines can push to AIKB (separate commits, no conflicts expected — different files)
- Nutanix Alerts folder scraping (Outlook) — same AppleScript target, just different folder name

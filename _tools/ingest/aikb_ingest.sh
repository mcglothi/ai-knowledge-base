#!/usr/bin/env bash
# AIKB Ingest Orchestrator — runs from WSL, called by Windows Task Scheduler
# Scrapes Outlook (via PS) + Teams (LevelDB) → generates AIKB docs → git push

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIKB_ROOT="/home/tmcglothin/code/AIKB"
STATE_FILE="$SCRIPT_DIR/.ingest_state.json"
LOG_FILE="$SCRIPT_DIR/ingest.log"
WIN_PS="powershell.exe"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== AIKB Ingest starting ==="

# Pull latest AIKB first
cd "$AIKB_ROOT"
git pull --quiet 2>/dev/null || log "WARN: git pull failed (continuing)"

# --- 1. OUTLOOK ---
log "Scraping Outlook..."
OUTLOOK_JSON="/mnt/c/Temp/aikb_last30.json"
if $WIN_PS -ExecutionPolicy Bypass -File "C:\\Temp\\aikb_outlook_ingest.ps1" > /tmp/outlook_ps.log 2>&1; then
    log "Outlook scrape OK"
else
    log "WARN: Outlook scrape failed (Outlook may not be running)"
fi

# --- 2. TEAMS LevelDB copy ---
log "Copying Teams LevelDB..."
TEAMS_LDB_WIN="C:\\Users\\tmcglothin\\AppData\\Local\\Packages\\MSTeams_8wekyb3d8bbwe\\LocalCache\\Microsoft\\MSTeams\\EBWebView\\WV2Profile_tfw\\IndexedDB\\https_teams.microsoft.com_0.indexeddb.leveldb"
TEAMS_LDB_DEST="/mnt/c/Temp/teams_leveldb"

$WIN_PS -ExecutionPolicy Bypass -Command "
\$src = '$TEAMS_LDB_WIN'
\$dst = 'C:\\Temp\\teams_leveldb'
if (Test-Path \$dst) { Remove-Item \$dst -Recurse -Force }
New-Item -ItemType Directory \$dst | Out-Null
Get-ChildItem \$src -Filter '*.ldb' | Copy-Item -Destination \$dst
Get-ChildItem \$src -Filter '*.log' | Copy-Item -Destination \$dst
Copy-Item \$src\\MANIFEST* \$dst -ErrorAction SilentlyContinue
Copy-Item \$src\\CURRENT \$dst -ErrorAction SilentlyContinue
Write-Output 'ok'
" > /tmp/teams_copy.log 2>&1 && log "Teams LDB copy OK" || log "WARN: Teams LDB copy failed"

# --- 3. Run analysis ---
log "Running analysis..."
python3 "$SCRIPT_DIR/teams_ingest.py" >> "$LOG_FILE" 2>&1 && log "Teams analysis OK" || log "WARN: Teams analysis failed"

if [ -f "$OUTLOOK_JSON" ]; then
    python3 "$SCRIPT_DIR/outlook_ingest.py" >> "$LOG_FILE" 2>&1 && log "Outlook analysis OK" || log "WARN: Outlook analysis failed"
fi

# --- 4. Git commit + push ---
log "Committing to AIKB..."
cd "$AIKB_ROOT"
if git diff --quiet && git diff --cached --quiet; then
    log "No changes to commit"
else
    git add work/teams-intel-last30.md work/infra-intel-last30.md 2>/dev/null || true
    git commit -m "AI Update: ingest run $(date '+%Y-%m-%d %H:%M') — email+teams intel refreshed" \
        && git push origin master \
        && log "Push OK" \
        || log "WARN: git push failed"
fi

# Update state
python3 -c "
import json, time
state = {'last_run': time.time(), 'last_run_str': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'}
with open('$STATE_FILE', 'w') as f: json.dump(state, f)
"

log "=== AIKB Ingest complete ==="

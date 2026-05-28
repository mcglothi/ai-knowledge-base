#!/usr/bin/env bash
# aikb-session-stop.sh — Claude Code Stop hook
# Runs automatically when a Claude Code session ends.
# Registered in ~/.claude/settings.json under hooks.Stop.
#
# Responsibilities:
#   1. Capture a structured session-end event to _runtime/events/
#   2. Run build_candidates.py to process any events from this session
#   3. Release this agent's active.md claim
#   4. Auto-commit uncommitted AIKB changes (non-destructive, best-effort)
#
# Claude Code passes a JSON payload on stdin — read it but don't fail if missing/malformed.

set -uo pipefail

# ── Locate AIKB root ─────────────────────────────────────────────────────────
HOME_DIR="${HOME:-$HOME}"
ROOT="${AIKB_ROOT:-}"
if [[ -z "$ROOT" ]]; then
  for candidate in "$HOME_DIR/code/AIKB" "$HOME_DIR/Code/AIKB"; do
    if [[ -d "$candidate/.git" ]]; then
      ROOT="$candidate"
      break
    fi
  done
fi
if [[ -z "$ROOT" || ! -d "$ROOT/.git" ]]; then
  echo "[aikb-stop] AIKB root not found, skipping." >&2
  exit 0
fi

PY="${PY_BIN:-$(command -v python3 2>/dev/null)}"
if [[ -z "$PY" ]]; then
  echo "[aikb-stop] python3 not found, skipping." >&2
  exit 0
fi

LOG_DIR="$ROOT/_runtime/maintenance"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/session-stop.log"
DATE_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%Y-%m-%dT%H:%M:%SZ)"

log() { echo "$DATE_UTC  $*" >> "$LOG"; }
run() { /usr/bin/timeout "${2:-20}s" bash -c "$1" >> "$LOG" 2>&1 || true; }

log "--- session stop begin (host=$(hostname))"

# ── Read Claude Code hook payload from stdin ─────────────────────────────────
PAYLOAD=""
if read -t 2 -r line 2>/dev/null; then
  PAYLOAD="$line"
  log "hook_payload_received: $(echo "$PAYLOAD" | head -c 200)"
fi

# Extract session_id from payload if present (best-effort jq or python fallback)
SESSION_ID=""
if command -v jq &>/dev/null && [[ -n "$PAYLOAD" ]]; then
  SESSION_ID="$(echo "$PAYLOAD" | jq -r '.session_id // empty' 2>/dev/null || true)"
fi
if [[ -z "$SESSION_ID" ]] && [[ -n "$PY" ]] && [[ -n "$PAYLOAD" ]]; then
  SESSION_ID="$( echo "$PAYLOAD" | "$PY" -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('session_id') or d.get('sessionId') or '')
except Exception:
    pass
" 2>/dev/null || true)"
fi
SESSION_ID="${SESSION_ID:-stop-hook-$(date -u +%Y%m%d%H%M%S)}"

# ── 1. Capture a session-end runtime event ────────────────────────────────────
run "cd '$ROOT' && '$PY' _tools/memory-pipeline/runtime_cli.py closeout \
  --agent 'Claude Code' \
  --session-id '$SESSION_ID' \
  --phrase 'Stop hook fired' \
  --note 'Automatic end-of-session capture via Claude Code Stop hook'" 25

# ── 2. Build candidates from today's events ───────────────────────────────────
run "cd '$ROOT' && '$PY' _tools/memory-pipeline/build_candidates.py \
  --date \$(date -u +%F)" 30

# ── 3. Release active.md session claim ───────────────────────────────────────
run "cd '$ROOT' && '$PY' _tools/memory-pipeline/runtime_cli.py release-session \
  --agent 'Claude Code'" 15

# ── 4. Auto-commit uncommitted AIKB changes (best-effort) ────────────────────
if [[ -d "$ROOT/.git" ]]; then
  DIRTY="$(git -C "$ROOT" status --porcelain 2>/dev/null | grep -v '^??' | head -1)"
  if [[ -n "$DIRTY" ]]; then
    run "git -C '$ROOT' add _runtime/ _agents/active.md && \
         git -C '$ROOT' commit -m 'AI Checkpoint: session stop — runtime events + candidate build' && \
         git -C '$ROOT' push origin main" 30
    log "auto-committed runtime changes"
  else
    # Still push if ahead of remote
    AHEAD="$(git -C "$ROOT" status --porcelain -b 2>/dev/null | grep 'ahead' | head -1)"
    if [[ -n "$AHEAD" ]]; then
      run "git -C '$ROOT' push origin main" 20
      log "pushed existing commits to remote"
    fi
  fi
fi

log "--- session stop end"
exit 0

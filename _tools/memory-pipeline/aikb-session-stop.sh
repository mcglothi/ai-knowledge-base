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

# Modes:
#   (default)  session end — Gemini SessionEnd, Claude SessionEnd: all steps.
#   --turn     Claude Stop fires after EVERY reply, and cmux tabs live for days;
#              skip closeout + release-session so claims survive the session.
set -uo pipefail
MODE=end; [[ "${1:-}" == "--turn" ]] && MODE=turn
# Last Updated: 2026-10-29
AGENT="${AIKB_AGENT:-Claude Code}"

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
# warn: goes to the log AND stderr, so Claude Code shows it instead of "No stderr output".
warn() { log "WARN: $*"; echo "[aikb-stop] $*" >&2; }
run() {
  "$PY" -c 'import subprocess,sys; sys.exit(subprocess.run(["bash", "-c", sys.argv[1]], timeout=int(sys.argv[2])).returncode)' \
    "$1" "${2:-20}" >> "$LOG" 2>&1
}

log "--- session stop begin (host=$(hostname) mode=$MODE)"

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

# Claude's per-reply Stop / SubagentStop events are turns, never session ends,
# even when settings.json registers this script without --turn. Unflagged
# Stop registrations wrote a fresh closeout event (and a checkpoint commit) on
# every reply -- 50-95 "session stop" commits a day on main.
HOOK_EVENT=""
if [[ -n "$PAYLOAD" ]]; then
  HOOK_EVENT="$(printf '%s' "$PAYLOAD" | "$PY" -c 'import sys,json
try: print(json.load(sys.stdin).get("hook_event_name") or "")
except Exception: pass' 2>/dev/null || true)"
fi
if [[ "$MODE" == end && ( "$HOOK_EVENT" == Stop || "$HOOK_EVENT" == SubagentStop ) ]]; then
  log "hook_event_name=$HOOK_EVENT is a turn, not a session end; running as --turn"
  MODE=turn
fi

# One closeout per real session: a session_id that already closed out is a repeat.
MARKERS="$(git -C "$ROOT" rev-parse --absolute-git-dir 2>/dev/null || echo "$ROOT/.git")/aikb-stop-sessions"
MARKER="$MARKERS/$(printf '%s' "$SESSION_ID" | tr -c 'A-Za-z0-9._-' '_')"
if [[ "$MODE" == end && -e "$MARKER" ]]; then
  log "session $SESSION_ID already closed out; skipping closeout + release"
  MODE=turn
fi

# ── 1. Capture a session-end runtime event ────────────────────────────────────
if [[ "$MODE" == end ]]; then
  run "cd '$ROOT' && '$PY' _tools/memory-pipeline/runtime_cli.py closeout \
    --agent '$AGENT' \
    --session-id '$SESSION_ID' \
    --phrase 'Stop hook fired' \
    --note 'Automatic end-of-session capture via AIKB Stop hook'" 25 \
    && { mkdir -p "$MARKERS"; touch "$MARKER"; find "$MARKERS" -type f -mtime +14 -delete 2>/dev/null; }
fi

# ── 2. Build candidates from today's events ───────────────────────────────────
run "cd '$ROOT' && '$PY' _tools/memory-pipeline/export_memory.py" 60 \
  || { warn "export_memory.py failed. Details: $LOG"; exit 1; }

# ── 3. Release active.md session claim ───────────────────────────────────────
[[ "$MODE" == end ]] && run "cd '$ROOT' && '$PY' _tools/memory-pipeline/runtime_cli.py release-session \
  --agent '$AGENT'" 15

# ── 4. Auto-commit uncommitted AIKB changes (best-effort) ────────────────────
# A nightly host may push artifacts to main, so a plain push is rejected whenever
# this host is behind. Pull --rebase first; on conflict, abort and keep the
# commits local (the next stop retries) rather than leave a half-done rebase.
sync_push() {
  run "git -C '$ROOT' push origin HEAD" 60 && return 0
  log "push rejected; rebasing onto upstream"
  if run "git -C '$ROOT' pull --rebase --autostash" 60; then
    run "git -C '$ROOT' push origin HEAD" 60 && return 0
  else
    run "git -C '$ROOT' rebase --abort" 15
  fi
  local behind
  behind="$(git -C "$ROOT" rev-list --count HEAD..@{u} 2>/dev/null || echo '?')"
  warn "push failed; local AIKB diverged from origin ($(git -C "$ROOT" rev-list --count @{u}..HEAD 2>/dev/null) ahead, $behind behind; commits kept locally). Conflicted files are in $LOG — resolve with one 'git merge origin/main', not a rebase."
  return 1
}

# Several agents (Claude Code, Codex, OpenCode wrappers) can stop at once;
# serialize the git section so concurrent rebases can't abort each other.
LOCK="$ROOT/.git/aikb-stop.lock"
if [[ -d "$LOCK" && -n "$(find "$LOCK" -maxdepth 0 -mmin +5 2>/dev/null)" ]]; then
  log "removing stale lock"; rmdir "$LOCK" 2>/dev/null
fi
GOT_LOCK=""
for _ in $(seq 1 30); do mkdir "$LOCK" 2>/dev/null && { GOT_LOCK=1; break; }; sleep 1; done
if [[ -z "$GOT_LOCK" ]]; then
  log "git section busy (another stop hook holds the lock); skipping — it will push"
  log "--- session stop end"
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

# A single nightly host is the writer of derived memory
# artifacts, so this hook never commits them. It also never discards them:
# _runtime/candidates and promotion-queue.md are where operators record review
# decisions, and the old "checkout HEAD -- <paths>" here silently threw those
# edits away on the next stop. Leave them for the operator to commit and say so.
# Extra nightly-owned paths can be added via AIKB_NIGHTLY_EXTRA_PATHS (space-separated).
NIGHTLY_PATHS=(_runtime/candidates _runtime/dreams _runtime/conflicts _runtime/graphs
  _runtime/events/compacted _runtime/promotion-queue.md)
# shellcheck disable=SC2206
[[ -n "${AIKB_NIGHTLY_EXTRA_PATHS:-}" ]] && NIGHTLY_PATHS+=(${AIKB_NIGHTLY_EXTRA_PATHS})
EXCLUDE=()
for p in "${NIGHTLY_PATHS[@]}"; do EXCLUDE+=(":(exclude)$p"); done
EXCLUDE_ARGS="$(printf "'%s' " "${EXCLUDE[@]}")"
if [[ -n "$(git -C "$ROOT" status --porcelain -- "${NIGHTLY_PATHS[@]}" 2>/dev/null | head -1)" ]]; then
  warn "uncommitted edits in nightly-owned paths left untouched and not auto-committed (manual review? commit them yourself). Details: $LOG"
  git -C "$ROOT" status --porcelain -- "${NIGHTLY_PATHS[@]}" >> "$LOG" 2>&1
fi

# Volatile telemetry rewritten on every run. Alone it is not worth a commit;
# it rides along with the next meaningful checkpoint instead.
VOLATILE_RE='^_runtime/(onwatch|maintenance)/'
if [[ -d "$ROOT/.git" ]]; then
  CHANGED="$(git -C "$ROOT" status --porcelain -uall -- _runtime/ _agents/active.md "${EXCLUDE[@]}" 2>/dev/null | cut -c4-)"
  DIRTY="$(printf '%s\n' "$CHANGED" | grep -v '^$' | grep -Ev "$VOLATILE_RE" | head -1)"
  if [[ -z "$DIRTY" && -n "$CHANGED" ]]; then
    log "only volatile telemetry changed; no checkpoint commit"
  fi
  if [[ -n "$DIRTY" ]]; then
    run "git -C '$ROOT' add -- _runtime/ _agents/active.md $EXCLUDE_ARGS && \
         git -C '$ROOT' commit -m 'AI Checkpoint: session stop — runtime events + candidate build'" 30 \
      || { warn "auto-commit failed. Details: $LOG"; exit 1; }
    log "auto-committed runtime changes"
    sync_push || exit 1
  else
    # Still push if ahead of remote
    AHEAD="$(git -C "$ROOT" status --porcelain -b 2>/dev/null | grep 'ahead' | head -1)"
    if [[ -n "$AHEAD" ]]; then
      sync_push || exit 1
      log "pushed existing commits to remote"
    fi
  fi
fi

log "--- session stop end"
exit 0

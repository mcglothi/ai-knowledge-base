#!/usr/bin/env bash
set -euo pipefail

# Fast best-effort maintenance for shutdown on intermittently-online hosts.

HOME_DIR="${HOME:-/home/mcglothi}"
ROOT="${AIKB_ROOT:-$HOME_DIR/code/AIKB}"
if [[ ! -d "$ROOT/.git" ]]; then
  for p in "$HOME_DIR/Code/AIKB" "$HOME_DIR/code/AIKB" "/home/mcglothi/code/AIKB" "/home/mcglothi/code/AIKB"; do
    if [[ -d "$p/.git" ]]; then
      ROOT="$p"
      break
    fi
  done
fi

PY_BIN="${PY_BIN:-$(command -v python3)}"
LOG_DIR="$ROOT/_runtime/maintenance"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/shutdown-finalize.log"

run_best_effort() {
  local cmd="$1"
  /usr/bin/timeout 20s bash -lc "$cmd" >>"$LOG_FILE" 2>&1 || true
}

{
  echo "---"
  date -u +"%Y-%m-%dT%H:%M:%SZ shutdown finalize start"
  echo "host=$(hostname) root=$ROOT py=$PY_BIN"
} >>"$LOG_FILE"

if [[ -d "$ROOT/.git" && -n "$PY_BIN" ]]; then
  run_best_effort "cd '$ROOT' && '$PY_BIN' _tools/memory-pipeline/build_candidates.py --date \$(date -u +%F)"
  run_best_effort "cd '$ROOT' && '$PY_BIN' _tools/memory-pipeline/autonomous_reorg.py --limit 20"
  run_best_effort "cd '$ROOT' && '$PY_BIN' _tools/memory-pipeline/queue_reorg_suggestions.py"
fi

{
  date -u +"%Y-%m-%dT%H:%M:%SZ shutdown finalize end"
} >>"$LOG_FILE"

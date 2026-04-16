#!/usr/bin/env bash
# codex-wrapper.sh — Wrap the Codex CLI so AIKB closeout runs on exit.
#
# Add to your shell config:
#   source /path/to/AIKB/_tools/memory-pipeline/codex-wrapper.sh
#
# This defines a shell function named `codex` that calls the real Codex
# binary, then launches aikb-session-stop.sh after Codex exits.

_AIKB_MP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_AIKB_STOP_SCRIPT="$_AIKB_MP_DIR/aikb-session-stop.sh"
_CODEX_REAL="$(command -v codex 2>/dev/null)"

if [[ -z "$_CODEX_REAL" || ! -x "$_AIKB_STOP_SCRIPT" ]]; then
  return 0 2>/dev/null || exit 0
fi

codex() {
  "$_CODEX_REAL" "$@"
  local _exit=$?
  bash "$_AIKB_STOP_SCRIPT" &
  return $_exit
}

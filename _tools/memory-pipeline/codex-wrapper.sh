#!/usr/bin/env bash
# codex-wrapper.sh — Wrap the Codex CLI so AIKB closeout runs on exit.
#
# Add to your shell config:
#   source /path/to/AIKB/_tools/memory-pipeline/codex-wrapper.sh
#
# This defines a shell function named `codex` that calls the real Codex
# binary, then launches aikb-session-stop.sh after Codex exits.
#
# Note: zsh has no BASH_SOURCE; inside a sourced file its $0 is the file path.
# Without the fallback, zsh resolved the stop script against $PWD, found
# nothing, and returned early — so `codex` was never wrapped.
#
# Uses `command codex` (not a stored path) for the same reason as
# opencode-wrapper.sh: re-sourcing makes `command -v codex` return the
# function name, which would recurse.

_AIKB_MP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
_AIKB_STOP_SCRIPT="$_AIKB_MP_DIR/aikb-session-stop.sh"

if ! command -v codex &>/dev/null || [[ ! -x "$_AIKB_STOP_SCRIPT" ]]; then
  return 0 2>/dev/null || exit 0
fi

codex() {
  command codex "$@"
  local _exit=$?
  # Background + stdin from /dev/null: the stop script `read`s a JSON payload,
  # and a background read from the terminal gets SIGTTIN-suspended.
  bash "$_AIKB_STOP_SCRIPT" </dev/null &
  return $_exit
}

#!/usr/bin/env bash
# copilot-wrapper.sh — Wrap the GitHub Copilot CLI so AIKB closeout runs on exit.
#
# Add to your shell config (~/.zshrc or ~/.bashrc):
#   source /path/to/AIKB/_tools/memory-pipeline/copilot-wrapper.sh
#
# This defines a shell function named `copilot` that calls the real Copilot
# binary, then launches aikb-session-stop.sh after Copilot exits.

_AIKB_MP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_AIKB_STOP_SCRIPT="$_AIKB_MP_DIR/aikb-session-stop.sh"
_COPILOT_REAL="$(command -v copilot 2>/dev/null)"

if [[ -z "$_COPILOT_REAL" || ! -x "$_AIKB_STOP_SCRIPT" ]]; then
  return 0 2>/dev/null || exit 0
fi

copilot() {
  "$_COPILOT_REAL" "$@"
  local _exit=$?
  bash "$_AIKB_STOP_SCRIPT" &
  return $_exit
}

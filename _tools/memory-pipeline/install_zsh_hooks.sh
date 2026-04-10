#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_FILE="$SCRIPT_DIR/aikb-shell-hooks.zsh"
ZSHRC="${HOME}/.zshrc"
SOURCE_LINE="source \"$HOOK_FILE\""

if [[ ! -f "$HOOK_FILE" ]]; then
  echo "Hook file not found: $HOOK_FILE" >&2
  exit 1
fi

touch "$ZSHRC"

if grep -Fq "$SOURCE_LINE" "$ZSHRC"; then
  echo "[aikb] ~/.zshrc already sources AIKB shell hooks"
else
  {
    echo
    echo "# AIKB runtime capture hooks"
    echo "$SOURCE_LINE"
  } >> "$ZSHRC"
  echo "[aikb] added AIKB shell hooks to ~/.zshrc"
fi

echo "[aikb] hook file: $HOOK_FILE"
echo "[aikb] restart the shell or run: source \"$HOOK_FILE\""

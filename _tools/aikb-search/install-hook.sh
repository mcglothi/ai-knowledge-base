#!/usr/bin/env bash
# Installs the AIKB search post-commit git hook.
# Run once from anywhere: bash _tools/aikb-search/install-hook.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIKB_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOOK_PATH="$AIKB_ROOT/.git/hooks/post-commit"

cat > "$HOOK_PATH" << 'HOOK'
#!/usr/bin/env bash
# AIKB Search — post-commit hook
# Rebuilds the semantic index in the background when .md files change.

AIKB_ROOT="$(git rev-parse --show-toplevel)"
TOOL_DIR="$AIKB_ROOT/_tools/aikb-search"
PYTHON="$TOOL_DIR/.venv/bin/python"

# Only trigger if .md files were part of this commit
if git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -q '\.md$'; then
    if [ -x "$PYTHON" ]; then
        "$PYTHON" "$TOOL_DIR/indexer.py" >> "$TOOL_DIR/index.log" 2>&1 &
        echo "[AIKB] Index rebuild triggered (background)"
    fi
fi
HOOK

chmod +x "$HOOK_PATH"
echo "Hook installed: $HOOK_PATH"

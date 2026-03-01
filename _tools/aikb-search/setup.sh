#!/usr/bin/env bash
# AIKB Search — one-command setup.
# Run from your AIKB repo after cloning or pulling:
#
#   bash _tools/aikb-search/setup.sh
#
# Idempotent — safe to re-run to upgrade dependencies or re-register the MCP server.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIKB_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV="$SCRIPT_DIR/.venv"

echo "=== AIKB Search Setup ==="
echo "AIKB root : $AIKB_ROOT"
echo "Tool dir  : $SCRIPT_DIR"

# ── 1. Find Python 3.10+ ──────────────────────────────────────────────────────
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" &>/dev/null; then
        ok=$("$candidate" -c 'import sys; print(sys.version_info >= (3, 10))' 2>/dev/null || echo False)
        if [ "$ok" = "True" ]; then
            PYTHON="$(command -v "$candidate")"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    echo "ERROR: Python 3.10+ not found."
    echo "  macOS: brew install python@3.11"
    echo "  Arch:  sudo pacman -S python"
    echo "  Debian/Ubuntu: sudo apt install python3.11"
    exit 1
fi

echo "Python    : $PYTHON ($("$PYTHON" --version))"

# ── 2. Create venv (skip if already exists) ───────────────────────────────────
if [ ! -d "$VENV" ]; then
    "$PYTHON" -m venv "$VENV"
    echo "Venv      : created at $VENV"
else
    echo "Venv      : exists at $VENV"
fi

# ── 3. Install / upgrade dependencies ────────────────────────────────────────
echo ""
echo "Installing dependencies..."
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
echo "Done."

# ── 4. Build the index ────────────────────────────────────────────────────────
echo ""
echo "Building search index (downloads ~23 MB model on first run)..."
"$VENV/bin/python" "$SCRIPT_DIR/indexer.py"

# ── 5. Install git post-commit hook ───────────────────────────────────────────
echo ""
bash "$SCRIPT_DIR/install-hook.sh"

# ── 6. Register MCP server with Claude Code ───────────────────────────────────
PYTHON_BIN="$VENV/bin/python"
SERVER_PY="$SCRIPT_DIR/server.py"

echo ""
if command -v claude &>/dev/null; then
    # Remove stale registration if it exists, then re-add with current paths
    claude mcp remove aikb-search -s user 2>/dev/null || true
    claude mcp add aikb-search -s user -- "$PYTHON_BIN" "$SERVER_PY"
    echo "MCP server registered: aikb-search"
else
    echo "Claude Code not found in PATH — skipping MCP registration."
    echo "To register manually once Claude Code is available:"
    echo ""
    echo "  claude mcp add aikb-search -s user -- \\"
    echo "    \"$PYTHON_BIN\" \\"
    echo "    \"$SERVER_PY\""
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "=== Setup complete ==="
echo "aikb_search is ready. Start a new Claude Code session to use it."

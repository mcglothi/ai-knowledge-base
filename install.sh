#!/usr/bin/env bash
# AIKB installer bootstrap.
# Checks for Python 3, then hands off to install.py (the real installer).

set -euo pipefail

# ── Windows detection ──────────────────────────────────────────────────────────
case "$(uname -s 2>/dev/null || echo unknown)" in
  MINGW*|MSYS*|CYGWIN*)
    echo ""
    echo "  AIKB requires WSL on Windows."
    echo "  Running inside Git Bash or Cygwin won't work reliably."
    echo ""
    echo "  Setup guide: docs/windows-wsl.md"
    echo "  Quick start:"
    echo "    1. Open PowerShell as Administrator"
    echo "    2. Run: wsl --install"
    echo "    3. Reboot, open the new Ubuntu app"
    echo "    4. Clone your repo inside WSL and re-run this script"
    echo ""
    exit 1
    ;;
esac

# ── Python check ───────────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    version=$("$cmd" -c "import sys; print(sys.version_info[:2])" 2>/dev/null || true)
    if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
      PYTHON="$cmd"
      break
    fi
  fi
done

if [[ -z "$PYTHON" ]]; then
  echo ""
  echo "  Python 3.8+ is required to run the AIKB installer."
  echo ""
  echo "  Install it:"
  echo "    macOS:   brew install python3"
  echo "    Ubuntu:  sudo apt install python3 python3-pip"
  echo "    Arch:    sudo pacman -S python"
  echo ""
  exit 1
fi

# ── Hand off to install.py ─────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR/install.py"
exec "$PYTHON" "$SCRIPT_DIR/install.py" "$@"

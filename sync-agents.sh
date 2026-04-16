#!/usr/bin/env bash
# Copy the personalized Codex instructions into one or more project repos.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_FILE="$SCRIPT_DIR/_agents/codex.md"

usage() {
  cat <<'EOF'
Usage: ./sync-agents.sh /path/to/project [/path/to/project...]

Each target may be either:
  - a project directory, in which case AGENTS.md will be written inside it
  - a direct path to the destination AGENTS.md file
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

if [[ ! -f "$SOURCE_FILE" ]]; then
  echo "Source file not found: $SOURCE_FILE" >&2
  exit 1
fi

for target in "$@"; do
  if [[ -d "$target" ]]; then
    dest="$target/AGENTS.md"
  else
    dest="$target"
    mkdir -p "$(dirname "$dest")"
  fi

  cp "$SOURCE_FILE" "$dest"
  echo "Synced Codex instructions -> $dest"
done

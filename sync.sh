#!/usr/bin/env bash
# =============================================================================
# AIKB Sync Script
# Pulls framework updates from the upstream template repo
# (mcglothi/ai-knowledge-base) and re-applies your personal configuration.
#
# Usage:
#   ./sync.sh           # interactive apply
#   ./sync.sh --check   # check-only, safe for periodic agent nudges
#   ./sync.sh --yes     # non-interactive apply
#
# What gets updated (framework dirs — safe to overwrite):
#   AGENTS.md  _agents/  _templates/  _tools/  docs/  _pending_approvals.md
#   CLAUDE.md  .github/copilot-instructions.md  sync.sh  sync-agents.sh  install.sh  .gitignore
#
# What is never touched (your personal content):
#   _index.md  _state.yaml  personal/  projects/  work/  and any other dirs
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { echo -e "${BLUE}→${RESET} $*"; }
success() { echo -e "${GREEN}✓${RESET} $*"; }
warn()    { echo -e "${YELLOW}⚠${RESET} $*"; }
error()   { echo -e "${RED}✗${RESET} $*" >&2; }
header()  { echo -e "\n${BOLD}$*${RESET}"; }

usage() {
  cat <<'EOF'
Usage: ./sync.sh [--check] [--yes] [--help]

  --check   Check for upstream framework updates and refresh local sync state.
  --yes     Apply updates without confirmation.
  --help    Show this help text.

The check-only mode is safe for agents to run periodically. It updates the
local template-sync state file but never changes tracked framework files.
EOF
}

CHECK_ONLY=0
AUTO_YES=0

for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    --yes) AUTO_YES=1 ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      error "Unknown argument: $arg"
      usage
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/.aikb-config.d"
STATE_FILE="$CONFIG_DIR/template-sync-state.json"
UPSTREAM_REMOTE="upstream"
UPSTREAM_URL="https://github.com/mcglothi/ai-knowledge-base.git"
DEFAULT_CHECK_INTERVAL_DAYS="${AIKB_TEMPLATE_CHECK_DAYS:-7}"
FRAMEWORK_PATHS=(
  "AGENTS.md"
  "CLAUDE.md"
  ".github/copilot-instructions.md"
  "_agents"
  "_templates"
  "_tools"
  "docs"
  "_pending_approvals.md"
  "sync.sh"
  "sync-agents.sh"
  "install.sh"
  ".gitignore"
)

header "AIKB Framework Sync"

if [[ ! -d "$CONFIG_DIR" ]]; then
  error "No saved config found at .aikb-config.d/"
  echo ""
  echo "  Run install.sh first to set up your personal configuration."
  echo "  It will save your settings so sync.sh can re-apply them."
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  error "python3 is required but not found."
  exit 1
fi

read_config() { cat "$CONFIG_DIR/$1" 2>/dev/null || echo ""; }

GITHUB_USERNAME=$(read_config GITHUB_USERNAME)
REPO_NAME=$(read_config REPO_NAME)
REPO_URL=$(read_config REPO_URL)
REPO_SSH=$(read_config REPO_SSH)
LOCAL_PATH=$(read_config LOCAL_PATH)
CODE_ROOT=$(read_config CODE_ROOT)
PRIMARY_HOSTNAME=$(read_config PRIMARY_HOSTNAME)
OS_FRIENDLY=$(read_config OS)
SECRETS_MANAGER=$(read_config SECRETS_MANAGER)
SECRETS_RETRIEVE=$(read_config SECRETS_RETRIEVE)
SETUP_CLAUDE=$(read_config SETUP_CLAUDE)
SETUP_GEMINI=$(read_config SETUP_GEMINI)

[[ -z "$REPO_URL" ]]    && REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
[[ -z "$REPO_SSH" ]]    && REPO_SSH="git@github.com:${GITHUB_USERNAME}/${REPO_NAME}.git"
[[ -z "$CODE_ROOT" ]]   && CODE_ROOT="$(dirname "$LOCAL_PATH")/"
[[ -z "$OS_FRIENDLY" ]] && { [[ "$(uname -s)" == "Darwin" ]] && OS_FRIENDLY="macOS" || OS_FRIENDLY="Linux"; }

if [[ -z "$GITHUB_USERNAME" ]]; then
  error "Saved config is incomplete. Re-run install.sh to rebuild it."
  exit 1
fi

read_state_field() {
  local key="$1"
  python3 - "$STATE_FILE" "$key" <<'PYEOF'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
if not path.exists():
    print("")
    raise SystemExit(0)
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print("")
    raise SystemExit(0)
value = data.get(key, "")
print("" if value is None else value)
PYEOF
}

write_sync_state() {
  local last_checked="$1"
  local last_seen="$2"
  local last_applied="$3"
  local interval_days="$4"

  python3 - "$STATE_FILE" "$last_checked" "$last_seen" "$last_applied" "$interval_days" <<'PYEOF'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
payload = {
    "last_checked_utc": sys.argv[2],
    "last_seen_upstream_sha": sys.argv[3],
    "last_applied_upstream_sha": sys.argv[4],
    "check_interval_days": int(sys.argv[5]),
}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PYEOF
}

current_utc() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

normalize_github_remote() {
  local url="$1"
  url="${url#git@github.com:}"
  url="${url#https://github.com/}"
  url="${url%.git}"
  printf '%s\n' "$url"
}

apply_substitutions() {
  local file="$1"
  [[ -f "$file" ]] || return 0

  python3 - "$file" \
    "$GITHUB_USERNAME" "$REPO_NAME" "$REPO_URL" "$REPO_SSH" \
    "$LOCAL_PATH" "$CODE_ROOT" "$PRIMARY_HOSTNAME" "$OS_FRIENDLY" \
    "$SECRETS_MANAGER" "$SECRETS_RETRIEVE" \
    <<'PYEOF'
import pathlib
import sys

f = pathlib.Path(sys.argv[1])
text = f.read_text(encoding="utf-8")

keys = [
    "GITHUB_USERNAME", "REPO_NAME", "REPO_URL", "REPO_SSH",
    "LOCAL_PATH", "CODE_ROOT", "PRIMARY_HOSTNAME", "OS",
    "SECRETS_MANAGER", "SECRETS_RETRIEVE",
]

for i, key in enumerate(keys):
    text = text.replace("{{" + key + "}}", sys.argv[i + 2])

f.write_text(text, encoding="utf-8")
PYEOF
}

collect_changed_paths() {
  local base_sha="$1"
  local file path
  local changed_files_text=""

  if [[ -n "$base_sha" ]]; then
    changed_files_text="$(git diff --name-only "${base_sha}..${UPSTREAM_REMOTE}/main" -- "${FRAMEWORK_PATHS[@]}" 2>/dev/null || true)"
  else
    changed_files_text="$(printf '%s\n' "${FRAMEWORK_PATHS[@]}")"
  fi

  for path in "${FRAMEWORK_PATHS[@]}"; do
    while IFS= read -r file; do
      [[ -z "$file" ]] && continue
      if [[ "$file" == "$path" || "$file" == "$path/"* ]]; then
        printf '%s\n' "$path"
        break
      fi
    done <<< "$changed_files_text"
  done
}

cd "$SCRIPT_DIR"
info "Config loaded: ${GITHUB_USERNAME}/${REPO_NAME} → ${LOCAL_PATH}"

header "Checking upstream remote..."
if git remote get-url "$UPSTREAM_REMOTE" &>/dev/null; then
  CURRENT_URL=$(git remote get-url "$UPSTREAM_REMOTE")
  CURRENT_NORM=$(normalize_github_remote "$CURRENT_URL")
  EXPECTED_NORM=$(normalize_github_remote "$UPSTREAM_URL")
  if [[ "$CURRENT_NORM" != "$EXPECTED_NORM" ]]; then
    warn "Upstream remote exists but points to: $CURRENT_URL"
    warn "Expected: $UPSTREAM_URL"
    if [[ "$CHECK_ONLY" -eq 1 ]]; then
      warn "Check-only mode will keep the current upstream remote."
    elif [[ "$AUTO_YES" -eq 1 ]]; then
      git remote set-url "$UPSTREAM_REMOTE" "$UPSTREAM_URL"
      success "Upstream remote updated"
    else
      read -rp "Update it? [y/N]: " FIX_REMOTE
      if [[ "$FIX_REMOTE" =~ ^[Yy] ]]; then
        git remote set-url "$UPSTREAM_REMOTE" "$UPSTREAM_URL"
        success "Upstream remote updated"
      fi
    fi
  else
    success "Upstream remote: $CURRENT_URL"
  fi
else
  git remote add "$UPSTREAM_REMOTE" "$UPSTREAM_URL"
  success "Added upstream remote → $UPSTREAM_URL"
fi

header "Fetching upstream..."
git fetch "$UPSTREAM_REMOTE" --quiet
success "Fetched upstream/main"

UPSTREAM_SHA=$(git rev-parse "${UPSTREAM_REMOTE}/main")
UPSTREAM_SHORT_SHA=$(git rev-parse --short "${UPSTREAM_REMOTE}/main")
LAST_CHECKED=$(read_state_field last_checked_utc)
LAST_SEEN_SHA=$(read_state_field last_seen_upstream_sha)
LAST_APPLIED_SHA=$(read_state_field last_applied_upstream_sha)
CHECK_INTERVAL_DAYS=$(read_state_field check_interval_days)
[[ -z "$CHECK_INTERVAL_DAYS" ]] && CHECK_INTERVAL_DAYS="$DEFAULT_CHECK_INTERVAL_DAYS"

SYNC_BASE_SHA="$LAST_APPLIED_SHA"
if [[ -z "$SYNC_BASE_SHA" ]]; then
  SYNC_BASE_SHA=$(git merge-base HEAD "${UPSTREAM_REMOTE}/main" 2>/dev/null || true)
fi

CHANGED=()
while IFS= read -r path; do
  [[ -n "$path" ]] && CHANGED+=("$path")
done < <(collect_changed_paths "$SYNC_BASE_SHA")
NOW_UTC=$(current_utc)

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  header "Template update check"
  echo "  Last checked : ${LAST_CHECKED:-never}"
  echo "  Last applied : ${LAST_APPLIED_SHA:-unknown}"
  echo "  Upstream SHA : ${UPSTREAM_SHORT_SHA}"
  echo "  Check window : every ${CHECK_INTERVAL_DAYS} day(s)"
  echo ""

  if [[ ${#CHANGED[@]} -eq 0 ]]; then
    success "No framework updates are waiting."
    write_sync_state "$NOW_UTC" "$UPSTREAM_SHA" "${LAST_APPLIED_SHA:-$UPSTREAM_SHA}" "$CHECK_INTERVAL_DAYS"
    exit 0
  fi

  warn "Framework updates are available:"
  for path in "${CHANGED[@]}"; do
    echo "  • $path"
  done
  echo ""
  echo "  To apply them interactively, run: ./sync.sh"
  echo "  To apply them non-interactively, run: ./sync.sh --yes"
  write_sync_state "$NOW_UTC" "$UPSTREAM_SHA" "${LAST_APPLIED_SHA:-}" "$CHECK_INTERVAL_DAYS"
  exit 0
fi

header "Changes in framework since last sync:"
echo ""

if [[ ${#CHANGED[@]} -eq 0 ]]; then
  success "Framework is already up to date."
  write_sync_state "$NOW_UTC" "$UPSTREAM_SHA" "${LAST_APPLIED_SHA:-$UPSTREAM_SHA}" "$CHECK_INTERVAL_DAYS"
  exit 0
fi

for path in "${CHANGED[@]}"; do
  echo "  • $path"
done

echo ""
echo "  Your personal dirs (personal/, projects/, work/, _index.md,"
echo "  _state.yaml, etc.) will not be touched."
echo ""

if [[ "$AUTO_YES" -ne 1 ]]; then
  read -rp "Apply these updates? [Y/n]: " CONFIRM
  CONFIRM="${CONFIRM:-Y}"
  if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then
    info "Aborted."
    write_sync_state "$NOW_UTC" "$UPSTREAM_SHA" "${LAST_APPLIED_SHA:-}" "$CHECK_INTERVAL_DAYS"
    exit 0
  fi
fi

header "Applying framework updates..."
for path in "${CHANGED[@]}"; do
  git checkout "${UPSTREAM_REMOTE}/main" -- "$path"
  success "Updated $path"
done

header "Re-applying your personal configuration..."
apply_substitutions "$SCRIPT_DIR/AGENTS.md"
[[ -f "$SCRIPT_DIR/CLAUDE.md" ]] && apply_substitutions "$SCRIPT_DIR/CLAUDE.md"
success "Personalized AGENTS.md"

apply_substitutions "$SCRIPT_DIR/.github/copilot-instructions.md"
success "Personalized Copilot instructions"

# Recursive: v2 overlays and shared L1 files live in _agents/v2/ and
# _agents/shared/ and must be personalized too.
while IFS= read -r tmpl; do
  apply_substitutions "$tmpl"
  success "Personalized ${tmpl#"$SCRIPT_DIR/"}"
done < <(find "$SCRIPT_DIR/_agents" -type f -name '*.md' | sort)

if [[ "$SETUP_CLAUDE" =~ ^[Yy] ]] && [[ -d "$HOME/.claude" ]]; then
  cp "$SCRIPT_DIR/_agents/claude-code.md" "$HOME/.claude/CLAUDE.md"
  success "Copied to ~/.claude/CLAUDE.md"
fi

if [[ "$SETUP_GEMINI" =~ ^[Yy] ]] && [[ -d "$HOME/.gemini" ]]; then
  cp "$SCRIPT_DIR/_agents/gemini-cli.md" "$HOME/.gemini/GEMINI.md"
  success "Copied to ~/.gemini/GEMINI.md"
fi

write_sync_state "$NOW_UTC" "$UPSTREAM_SHA" "$UPSTREAM_SHA" "$CHECK_INTERVAL_DAYS"

header "Committing..."
git add "${CHANGED[@]}"

if git diff --cached --quiet; then
  info "Framework files already match the target state; no commit created."
else
  git commit -m "chore: sync framework from upstream @ ${UPSTREAM_SHORT_SHA}"
  success "Committed sync"
fi

header "Done!"
echo ""
echo "  Framework updated to upstream @ ${UPSTREAM_SHORT_SHA}"
echo ""
echo "  Next steps:"
echo "   • Push to your private repo:  git push origin main"
echo "   • Re-check later without applying:  ./sync.sh --check"
  echo "   • Re-sync project agent files: ./sync-agents.sh --all /path/to/project [/path/to/project...]"
if [[ ! "$SETUP_CLAUDE" =~ ^[Yy] ]]; then
  echo "   • Sync Claude Code:  cp _agents/claude-code.md ~/.claude/CLAUDE.md"
fi
if [[ ! "$SETUP_GEMINI" =~ ^[Yy] ]]; then
  echo "   • Sync Gemini CLI:   cp _agents/gemini-cli.md ~/.gemini/GEMINI.md"
fi
echo "   • Re-paste into Cursor/ChatGPT/Gemini/Grok if those are configured"
echo ""

# Post-sync notes: surface one-time migration steps tied to the framework
# paths that actually changed (docs/post-sync-notes.conf: `pattern|message`).
NOTES_FILE="$SCRIPT_DIR/docs/post-sync-notes.conf"
if [[ -f "$NOTES_FILE" ]]; then
  PRINTED_NOTES_HEADER=0
  while IFS='|' read -r pattern note; do
    [[ -z "$pattern" || "$pattern" == \#* ]] && continue
    for path in "${CHANGED[@]}"; do
      if [[ "$path" == $pattern ]]; then
        if [[ "$PRINTED_NOTES_HEADER" -eq 0 ]]; then
          header "Post-sync steps required:"
          PRINTED_NOTES_HEADER=1
        fi
        warn "$note"
        break
      fi
    done
  done < "$NOTES_FILE"
  [[ "$PRINTED_NOTES_HEADER" -eq 1 ]] && echo ""
fi

#!/usr/bin/env bash
# =============================================================================
# AIKB Sync Script
# Pulls framework updates from the upstream template repo
# (mcglothi/ai-knowledge-base) and re-applies your personal configuration.
#
# Usage: chmod +x sync.sh && ./sync.sh
#
# What gets updated (framework dirs — safe to overwrite):
#   _agents/  _templates/  docs/  sync.sh  install.sh  .gitignore
#
# What is never touched (your personal content):
#   _index.md  _state.yaml  personal/  projects/  work/  and any other dirs
# =============================================================================

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/.aikb-config.d"
UPSTREAM_REMOTE="upstream"
UPSTREAM_URL="https://github.com/mcglothi/ai-knowledge-base.git"

# Framework paths — these are pulled from upstream and re-personalized
FRAMEWORK_PATHS=("_agents" "_templates" "docs" "sync.sh" "install.sh" ".gitignore")

# ── Check prerequisites ───────────────────────────────────────────────────────
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

# ── Load saved config ─────────────────────────────────────────────────────────
read_config() { cat "$CONFIG_DIR/$1" 2>/dev/null || echo ""; }

GITHUB_USERNAME=$(read_config GITHUB_USERNAME)
REPO_NAME=$(read_config REPO_NAME)
LOCAL_PATH=$(read_config LOCAL_PATH)
PRIMARY_HOSTNAME=$(read_config PRIMARY_HOSTNAME)
SECRETS_MANAGER=$(read_config SECRETS_MANAGER)
SECRETS_RETRIEVE=$(read_config SECRETS_RETRIEVE)
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
REPO_SSH="git@github.com:${GITHUB_USERNAME}/${REPO_NAME}.git"
SETUP_CLAUDE=$(read_config SETUP_CLAUDE || echo "n")
SETUP_GEMINI=$(read_config SETUP_GEMINI || echo "n")

if [[ -z "$GITHUB_USERNAME" ]]; then
  error "Saved config is incomplete. Re-run install.sh to rebuild it."
  exit 1
fi

info "Config loaded: ${GITHUB_USERNAME}/${REPO_NAME} → ${LOCAL_PATH}"

# ── Add/verify upstream remote ────────────────────────────────────────────────
header "Checking upstream remote..."
cd "$SCRIPT_DIR"

if git remote get-url "$UPSTREAM_REMOTE" &>/dev/null; then
  CURRENT_URL=$(git remote get-url "$UPSTREAM_REMOTE")
  if [[ "$CURRENT_URL" != "$UPSTREAM_URL" ]]; then
    warn "Upstream remote exists but points to: $CURRENT_URL"
    warn "Expected: $UPSTREAM_URL"
    read -rp "Update it? [y/N]: " FIX_REMOTE
    if [[ "$FIX_REMOTE" =~ ^[Yy] ]]; then
      git remote set-url "$UPSTREAM_REMOTE" "$UPSTREAM_URL"
      success "Upstream remote updated"
    fi
  else
    success "Upstream remote: $UPSTREAM_URL"
  fi
else
  git remote add "$UPSTREAM_REMOTE" "$UPSTREAM_URL"
  success "Added upstream remote → $UPSTREAM_URL"
fi

# ── Fetch upstream ────────────────────────────────────────────────────────────
header "Fetching upstream..."
git fetch "$UPSTREAM_REMOTE" --quiet
success "Fetched upstream/main"

# ── Show what changed ─────────────────────────────────────────────────────────
header "Changes in framework since last sync:"
echo ""

CHANGED=()
for path in "${FRAMEWORK_PATHS[@]}"; do
  # Compare upstream version to what's currently in the working tree
  if git diff --quiet "${UPSTREAM_REMOTE}/main" -- "$path" 2>/dev/null; then
    : # no change
  else
    CHANGED+=("$path")
  fi
done

if [[ ${#CHANGED[@]} -eq 0 ]]; then
  success "Framework is already up to date."
  exit 0
fi

for path in "${CHANGED[@]}"; do
  echo "  • $path"
done

echo ""
echo "  Your personal dirs (personal/, projects/, work/, _index.md,"
echo "  _state.yaml, etc.) will not be touched."
echo ""
read -rp "Apply these updates? [Y/n]: " CONFIRM
CONFIRM="${CONFIRM:-Y}"
if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then
  info "Aborted."
  exit 0
fi

# ── Apply upstream changes ────────────────────────────────────────────────────
header "Applying framework updates..."

for path in "${CHANGED[@]}"; do
  git checkout "${UPSTREAM_REMOTE}/main" -- "$path"
  success "Updated $path"
done

# ── Re-apply placeholder substitution ────────────────────────────────────────
header "Re-applying your personal configuration..."

apply_substitutions() {
  local file="$1"
  [[ -f "$file" ]] || return 0

  python3 - "$file" \
    "$GITHUB_USERNAME" "$REPO_NAME" "$REPO_URL" "$REPO_SSH" \
    "$LOCAL_PATH" "$PRIMARY_HOSTNAME" "$SECRETS_MANAGER" "$SECRETS_RETRIEVE" \
    <<'PYEOF'
import sys, pathlib

f = pathlib.Path(sys.argv[1])
text = f.read_text()

keys = [
    'GITHUB_USERNAME', 'REPO_NAME', 'REPO_URL', 'REPO_SSH',
    'LOCAL_PATH', 'PRIMARY_HOSTNAME', 'SECRETS_MANAGER', 'SECRETS_RETRIEVE',
]

for i, key in enumerate(keys):
    text = text.replace('{{' + key + '}}', sys.argv[i + 2])

f.write_text(text)
PYEOF
}

for tmpl in "$SCRIPT_DIR/_agents"/*.md; do
  apply_substitutions "$tmpl"
  success "Personalized $(basename "$tmpl")"
done

# ── Re-sync to AI tool config locations ──────────────────────────────────────
if [[ "$SETUP_CLAUDE" =~ ^[Yy] ]] && [[ -d "$HOME/.claude" ]]; then
  cp "$SCRIPT_DIR/_agents/claude-code.md" "$HOME/.claude/CLAUDE.md"
  success "Copied to ~/.claude/CLAUDE.md"
fi

if [[ "$SETUP_GEMINI" =~ ^[Yy] ]] && [[ -d "$HOME/.gemini" ]]; then
  cp "$SCRIPT_DIR/_agents/gemini-cli.md" "$HOME/.gemini/GEMINI.md"
  success "Copied to ~/.gemini/GEMINI.md"
fi

# ── Commit the sync ───────────────────────────────────────────────────────────
header "Committing..."
git add "${CHANGED[@]}"

# Get the upstream commit SHA for reference
UPSTREAM_SHA=$(git rev-parse --short "${UPSTREAM_REMOTE}/main")
git commit -m "chore: sync framework from upstream @ ${UPSTREAM_SHA}"
success "Committed sync"

# ── Next steps ────────────────────────────────────────────────────────────────
header "Done!"
echo ""
echo "  Framework updated to upstream @ ${UPSTREAM_SHA}"
echo ""
echo "  Next steps:"
echo "   • Push to your private repo:  git push origin main"
if [[ ! "$SETUP_CLAUDE" =~ ^[Yy] ]]; then
  echo "   • Sync Claude Code:  cp _agents/claude-code.md ~/.claude/CLAUDE.md"
fi
if [[ ! "$SETUP_GEMINI" =~ ^[Yy] ]]; then
  echo "   • Sync Gemini CLI:   cp _agents/gemini-cli.md ~/.gemini/GEMINI.md"
fi
echo "   • Re-paste into Cursor/ChatGPT/Gemini/Grok if those are configured"
echo ""

#!/usr/bin/env bash
# =============================================================================
# AIKB Setup Script
# Personalizes agent instruction files with your GitHub username, repo name,
# and local path after you've cloned the template.
#
# Usage: chmod +x install.sh && ./install.sh
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

# ── Detect OS and shell ───────────────────────────────────────────────────────
OS=$(uname -s)
SHELL_NAME=$(basename "${SHELL:-bash}")

case "$OS" in
  Darwin) OS_FRIENDLY="macOS" ;;
  Linux)  OS_FRIENDLY="Linux" ;;
  *)      OS_FRIENDLY="$OS" ;;
esac

# ── Prerequisites check ───────────────────────────────────────────────────────
header "Checking prerequisites..."

if ! command -v git &>/dev/null; then
  error "git is required but not installed. Install it and re-run."
  exit 1
fi
success "git found ($(git --version | cut -d' ' -f3))"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Collect configuration ─────────────────────────────────────────────────────
header "AIKB Configuration"
echo "This script will personalize your agent instruction files."
echo "No credentials will be collected or stored."
echo ""

# GitHub username
read -rp "GitHub username: " GITHUB_USERNAME
if [[ -z "$GITHUB_USERNAME" ]]; then
  error "GitHub username is required."
  exit 1
fi

# Repo name
read -rp "AIKB repo name [AIKB]: " REPO_NAME
REPO_NAME="${REPO_NAME:-AIKB}"

# Local clone path
DEFAULT_PATH="$HOME/AIKB"
if [[ "$OS" == "Darwin" ]]; then
  DEFAULT_PATH="$HOME/Code/AIKB"
fi
read -rp "Local clone path [$DEFAULT_PATH]: " LOCAL_PATH
LOCAL_PATH="${LOCAL_PATH:-$DEFAULT_PATH}"

# Hostname (for machine table)
DEFAULT_HOSTNAME=$(hostname -s 2>/dev/null || hostname)
read -rp "Primary machine hostname [$DEFAULT_HOSTNAME]: " PRIMARY_HOSTNAME
PRIMARY_HOSTNAME="${PRIMARY_HOSTNAME:-$DEFAULT_HOSTNAME}"

# Secrets manager (informational only — affects docs/comments in generated files)
echo ""
echo "What secrets manager do you use? (used only to tailor comments in generated files)"
echo "  1) 1Password"
echo "  2) Bitwarden / Vaultwarden"
echo "  3) macOS Keychain"
echo "  4) Environment variables (.env / shell profile)"
echo "  5) Other / skip"
read -rp "Choice [5]: " SECRETS_CHOICE
SECRETS_CHOICE="${SECRETS_CHOICE:-5}"

case "$SECRETS_CHOICE" in
  1) SECRETS_MANAGER="1Password" ; SECRETS_RETRIEVE='op read "op://Private/ITEM_NAME/credential"' ;;
  2) SECRETS_MANAGER="Bitwarden"  ; SECRETS_RETRIEVE='bw get password "PAT/<Service>/<Name>" --session "$BW_SESSION"' ;;
  3) SECRETS_MANAGER="macOS Keychain" ; SECRETS_RETRIEVE='security find-generic-password -w -a "$USER" -s "ITEM_NAME"' ;;
  4) SECRETS_MANAGER="Environment variables" ; SECRETS_RETRIEVE='echo "$MY_SECRET_VAR"' ;;
  *) SECRETS_MANAGER="your secrets manager" ; SECRETS_RETRIEVE="[see your secrets manager documentation]" ;;
esac

# ── Derive values ─────────────────────────────────────────────────────────────
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
REPO_SSH="git@github.com:${GITHUB_USERNAME}/${REPO_NAME}.git"
CODE_ROOT="$(dirname "$LOCAL_PATH")/"

header "Configuration summary"
echo "  GitHub username : $GITHUB_USERNAME"
echo "  Repo name       : $REPO_NAME"
echo "  Repo URL        : $REPO_URL"
echo "  Local path      : $LOCAL_PATH"
echo "  Hostname        : $PRIMARY_HOSTNAME"
echo "  Secrets manager : $SECRETS_MANAGER"
echo ""
read -rp "Proceed? [Y/n]: " CONFIRM
CONFIRM="${CONFIRM:-Y}"
if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then
  info "Aborted."
  exit 0
fi

# ── Substitute placeholders in agent files ────────────────────────────────────
header "Generating agent instruction files..."

AGENTS_DIR="$SCRIPT_DIR/_agents"

# We use a temp directory to write substituted versions, then move them.
# This avoids partial writes on failure.
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

for tmpl in "$AGENTS_DIR"/*.md; do
  fname=$(basename "$tmpl")
  out="$TMP_DIR/$fname"

  sed \
    -e "s|{{GITHUB_USERNAME}}|$GITHUB_USERNAME|g" \
    -e "s|{{REPO_NAME}}|$REPO_NAME|g" \
    -e "s|{{REPO_URL}}|$REPO_URL|g" \
    -e "s|{{REPO_SSH}}|$REPO_SSH|g" \
    -e "s|{{LOCAL_PATH}}|$LOCAL_PATH|g" \
    -e "s|{{CODE_ROOT}}|$CODE_ROOT|g" \
    -e "s|{{PRIMARY_HOSTNAME}}|$PRIMARY_HOSTNAME|g" \
    -e "s|{{OS}}|$OS_FRIENDLY|g" \
    -e "s|{{SECRETS_MANAGER}}|$SECRETS_MANAGER|g" \
    -e "s|{{SECRETS_RETRIEVE}}|$SECRETS_RETRIEVE|g" \
    "$tmpl" > "$out"

  cp "$out" "$tmpl"
  success "Updated _agents/$fname"
done

# ── Update _index.md placeholder ─────────────────────────────────────────────
if grep -q "{{GITHUB_USERNAME}}" "$SCRIPT_DIR/_index.md" 2>/dev/null; then
  sed -i.bak \
    -e "s|{{GITHUB_USERNAME}}|$GITHUB_USERNAME|g" \
    -e "s|{{REPO_NAME}}|$REPO_NAME|g" \
    "$SCRIPT_DIR/_index.md" && rm -f "$SCRIPT_DIR/_index.md.bak"
  success "Updated _index.md"
fi

# ── Scaffold personal profile files ──────────────────────────────────────────
header "Scaffolding personal files..."

if [[ ! -f "$SCRIPT_DIR/personal/profile.md" ]]; then
  cp "$SCRIPT_DIR/example/personal/profile.md" "$SCRIPT_DIR/personal/profile.md"
  success "Created personal/profile.md  ← fill this in"
fi

mkdir -p "$SCRIPT_DIR/personal/dev-environment"
if [[ ! -f "$SCRIPT_DIR/personal/dev-environment/README.md" ]]; then
  sed "s/my-macbook/$PRIMARY_HOSTNAME/g" \
    "$SCRIPT_DIR/example/personal/dev-environment.md" \
    > "$SCRIPT_DIR/personal/dev-environment/README.md"
  success "Created personal/dev-environment/README.md  ← fill this in"
fi

MACHINE_PROFILE="$SCRIPT_DIR/personal/dev-environment/${PRIMARY_HOSTNAME}.md"
if [[ ! -f "$MACHINE_PROFILE" ]]; then
  sed "s/\[hostname\]/$PRIMARY_HOSTNAME/g" \
    "$SCRIPT_DIR/_templates/machine-profile.md" > "$MACHINE_PROFILE"
  success "Created personal/dev-environment/${PRIMARY_HOSTNAME}.md  ← fill this in"
fi

# ── Save config for future syncs ─────────────────────────────────────────────
header "Saving configuration..."
mkdir -p "$SCRIPT_DIR/.aikb-config.d"
printf '%s' "$GITHUB_USERNAME"   > "$SCRIPT_DIR/.aikb-config.d/GITHUB_USERNAME"
printf '%s' "$REPO_NAME"         > "$SCRIPT_DIR/.aikb-config.d/REPO_NAME"
printf '%s' "$REPO_URL"          > "$SCRIPT_DIR/.aikb-config.d/REPO_URL"
printf '%s' "$REPO_SSH"          > "$SCRIPT_DIR/.aikb-config.d/REPO_SSH"
printf '%s' "$LOCAL_PATH"        > "$SCRIPT_DIR/.aikb-config.d/LOCAL_PATH"
printf '%s' "$CODE_ROOT"         > "$SCRIPT_DIR/.aikb-config.d/CODE_ROOT"
printf '%s' "$PRIMARY_HOSTNAME"  > "$SCRIPT_DIR/.aikb-config.d/PRIMARY_HOSTNAME"
printf '%s' "$OS_FRIENDLY"       > "$SCRIPT_DIR/.aikb-config.d/OS"
printf '%s' "$SECRETS_MANAGER"   > "$SCRIPT_DIR/.aikb-config.d/SECRETS_MANAGER"
printf '%s' "$SECRETS_RETRIEVE"  > "$SCRIPT_DIR/.aikb-config.d/SECRETS_RETRIEVE"
success "Config saved to .aikb-config.d/ (git-ignored)"

# ── Add upstream remote for future framework syncs ────────────────────────────
git remote add upstream https://github.com/mcglothi/ai-knowledge-base.git 2>/dev/null \
  && success "Added upstream remote → mcglothi/ai-knowledge-base" \
  || info "Upstream remote already configured"

# ── Initial git commit ────────────────────────────────────────────────────────
header "Creating initial commit..."
cd "$SCRIPT_DIR"
git add -A
git commit -m "chore: personalize AIKB for $GITHUB_USERNAME" --allow-empty
success "Initial commit created"

# ── Claude Code integration (optional) ───────────────────────────────────────
SETUP_CLAUDE="n"
if command -v claude &>/dev/null; then
  echo ""
  read -rp "Claude Code detected. Copy agent instructions to ~/.claude/CLAUDE.md? [Y/n]: " SETUP_CLAUDE
  SETUP_CLAUDE="${SETUP_CLAUDE:-Y}"
  if [[ "$SETUP_CLAUDE" =~ ^[Yy] ]]; then
    mkdir -p "$HOME/.claude"
    cp "$AGENTS_DIR/claude-code.md" "$HOME/.claude/CLAUDE.md"
    success "Copied to ~/.claude/CLAUDE.md"
  fi
fi
printf '%s' "$SETUP_CLAUDE" > "$SCRIPT_DIR/.aikb-config.d/SETUP_CLAUDE"

# ── Gemini CLI integration (optional) ────────────────────────────────────────
SETUP_GEMINI="n"
if command -v gemini &>/dev/null; then
  echo ""
  read -rp "Gemini CLI detected. Copy agent instructions to ~/.gemini/GEMINI.md? [Y/n]: " SETUP_GEMINI
  SETUP_GEMINI="${SETUP_GEMINI:-Y}"
  if [[ "$SETUP_GEMINI" =~ ^[Yy] ]]; then
    mkdir -p "$HOME/.gemini"
    cp "$AGENTS_DIR/gemini-cli.md" "$HOME/.gemini/GEMINI.md"
    success "Copied to ~/.gemini/GEMINI.md"
  fi
fi
printf '%s' "$SETUP_GEMINI" > "$SCRIPT_DIR/.aikb-config.d/SETUP_GEMINI"

# ── Next steps ────────────────────────────────────────────────────────────────
header "Done! Next steps:"
echo ""
echo "  1. Push to GitHub:"
echo "     git push origin main"
echo ""
echo "  2. Configure your AI tools:"
echo "     • Claude Code / Gemini CLI — done if you accepted above"
echo "     • Cursor — paste _agents/cursor.md into Settings → Rules → User Rules"
echo "     • ChatGPT — paste _agents/chatgpt.md into Settings → Custom Instructions"
echo "     • Gemini — paste _agents/gemini.md into Settings → Custom Instructions"
echo ""
echo "  3. (Optional) Set up the GitHub MCP server for remote access:"
echo "     See docs/mcp-setup.md"
echo ""
echo "  4. Fill in your personal profile (files are already created, just need your details):"
echo "     • personal/profile.md — your background, skills, preferences"
echo "     • personal/dev-environment/README.md — machine inventory"
echo "     • personal/dev-environment/${PRIMARY_HOSTNAME}.md — installed tools on this machine"
echo ""
echo "  5. (Optional) Set up the GitHub MCP server for remote AIKB access:"
echo "     See docs/mcp-setup.md"
echo ""
echo "  6. On a new machine, clone your private AIKB repo and run install.sh again."
echo "     It will detect the new hostname and scaffold a machine profile for it."
echo "     Your existing personalization is already committed — no re-entering needed."
echo ""
echo "  7. To pull future framework updates from the template:"
echo "     ./sync.sh  (re-applies your personal config automatically)"
echo ""
success "AIKB is ready. Happy building!"

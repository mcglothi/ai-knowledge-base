#!/usr/bin/env bash
# Sync AIKB agent instruction files to tool configs, project repos, or another AIKB/template checkout.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$SCRIPT_DIR/_agents"

ALL_AGENTS=(
  "claude-code"
  "gemini-cli"
  "codex"
  "copilot"
  "opencode"
  "cursor"
  "chatgpt"
  "gemini"
  "grok"
)

usage() {
  cat <<'EOF'
Usage:
  ./sync-agents.sh [target ...]
  ./sync-agents.sh --agent <name> [--agent <name> ...] [--global] [target ...]
  ./sync-agents.sh --all [--global] [target ...]
  ./sync-agents.sh --list

Defaults:
  With no --agent/--all, syncs Codex to each target's AGENTS.md.

Targets:
  - Project directory: writes repo-native files for selected agents.
      codex   -> AGENTS.md
      copilot -> .github/copilot-instructions.md
  - AIKB/template checkout with _agents/: also refreshes selected _agents/*.md.
  - Direct file path: only valid with one selected agent.

Global:
  --global copies file-backed tool configs when possible:
      claude-code -> ~/.claude/CLAUDE.md
      gemini-cli  -> ~/.gemini/GEMINI.md
      codex       -> ~/.codex/AGENTS.md

Agent names: claude-code, gemini-cli, codex, copilot, opencode, cursor,
chatgpt, gemini, grok. Aliases: claude, gemini_cli, github-copilot.
EOF
}

canonical_agent() {
  case "$1" in
    claude|claude-code) echo "claude-code" ;;
    gemini-cli|gemini_cli) echo "gemini-cli" ;;
    github-copilot|copilot) echo "copilot" ;;
    codex|opencode|cursor|chatgpt|gemini|grok) echo "$1" ;;
    *)
      echo "Unknown agent: $1" >&2
      return 1
      ;;
  esac
}

agent_file() {
  case "$1" in
    claude-code) echo "claude-code.md" ;;
    gemini-cli) echo "gemini-cli.md" ;;
    codex) echo "codex.md" ;;
    copilot) echo "copilot.md" ;;
    opencode) echo "opencode.md" ;;
    cursor) echo "cursor.md" ;;
    chatgpt) echo "chatgpt.md" ;;
    gemini) echo "gemini.md" ;;
    grok) echo "grok.md" ;;
  esac
}

copy_agent_source() {
  local agent="$1"
  local dest_dir="$2"
  local src="$AGENTS_DIR/$(agent_file "$agent")"
  local dest="$dest_dir/$(agent_file "$agent")"

  if [[ ! -f "$src" ]]; then
    echo "Missing source for $agent: $src" >&2
    exit 1
  fi

  mkdir -p "$dest_dir"
  if [[ -f "$dest" && "$(realpath "$src")" == "$(realpath "$dest")" ]]; then
    echo "Skipped $agent source -> $dest (same file)"
    return 0
  fi
  cp "$src" "$dest"
  echo "Synced $agent source -> $dest"
}

sync_project_agent() {
  local agent="$1"
  local target="$2"
  local src="$AGENTS_DIR/$(agent_file "$agent")"
  local dest

  case "$agent" in
    codex)
      dest="$target/AGENTS.md"
      ;;
    copilot)
      dest="$target/.github/copilot-instructions.md"
      ;;
    *)
      return 0
      ;;
  esac

  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  echo "Synced $agent project instructions -> $dest"
}

sync_global_agent() {
  local agent="$1"
  local src="$AGENTS_DIR/$(agent_file "$agent")"
  local dest=""

  case "$agent" in
    claude-code) dest="$HOME/.claude/CLAUDE.md" ;;
    gemini-cli) dest="$HOME/.gemini/GEMINI.md" ;;
    codex) dest="$HOME/.codex/AGENTS.md" ;;
    copilot)
      echo "Skipped copilot global sync: use a project target for .github/copilot-instructions.md"
      return 0
      ;;
    opencode)
      echo "Skipped opencode copy: point opencode.json instructions at $src"
      return 0
      ;;
    cursor|chatgpt|gemini|grok)
      echo "Skipped $agent copy: paste $src into that tool's settings UI"
      return 0
      ;;
  esac

  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  echo "Synced $agent global instructions -> $dest"
}

SELECTED=()
TARGETS=()
SYNC_GLOBAL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --list)
      printf '%s\n' "${ALL_AGENTS[@]}"
      exit 0
      ;;
    --all)
      SELECTED=("${ALL_AGENTS[@]}")
      shift
      ;;
    --agent)
      [[ $# -ge 2 ]] || { echo "--agent requires a name" >&2; exit 1; }
      SELECTED+=("$(canonical_agent "$2")")
      shift 2
      ;;
    --global)
      SYNC_GLOBAL=1
      shift
      ;;
    --)
      shift
      TARGETS+=("$@")
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
    *)
      TARGETS+=("$1")
      shift
      ;;
  esac
done

if [[ ${#SELECTED[@]} -eq 0 ]]; then
  SELECTED=("codex")
fi

for agent in "${SELECTED[@]}"; do
  src="$AGENTS_DIR/$(agent_file "$agent")"
  [[ -f "$src" ]] || { echo "Missing source for $agent: $src" >&2; exit 1; }
done

if [[ "$SYNC_GLOBAL" -eq 1 ]]; then
  for agent in "${SELECTED[@]}"; do
    sync_global_agent "$agent"
  done
fi

if [[ ${#TARGETS[@]} -eq 0 && "$SYNC_GLOBAL" -eq 0 ]]; then
  usage
  exit 1
fi

for target in "${TARGETS[@]}"; do
  if [[ -d "$target" ]]; then
    copy_sources=0
    if [[ -d "$target/_agents" ]]; then
      copy_sources=1
    fi

    if [[ "$copy_sources" -eq 1 ]]; then
      for agent in "${SELECTED[@]}"; do
        copy_agent_source "$agent" "$target/_agents"
      done
    fi

    for agent in "${SELECTED[@]}"; do
      sync_project_agent "$agent" "$target"
    done
  else
    if [[ ${#SELECTED[@]} -ne 1 ]]; then
      echo "Direct file targets require exactly one selected agent." >&2
      exit 1
    fi
    agent="${SELECTED[0]}"
    src="$AGENTS_DIR/$(agent_file "$agent")"
    mkdir -p "$(dirname "$target")"
    cp "$src" "$target"
    echo "Synced $agent instructions -> $target"
  fi
done

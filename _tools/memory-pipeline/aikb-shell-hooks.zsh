#!/usr/bin/env zsh
# Opt-in shell hooks for high-signal AIKB runtime capture.

if [[ -n "${AIKB_HOOKS_LOADED:-}" ]]; then
  return 0
fi
typeset -g AIKB_HOOKS_LOADED=1

autoload -Uz add-zsh-hook

_aikb_detect_root() {
  local candidates=(
    "$HOME/code/AIKB"
    "$HOME/Code/AIKB"
  )
  local cand
  for cand in "${candidates[@]}"; do
    [[ -d "$cand/.git" ]] && { echo "$cand"; return 0; }
  done
  return 1
}

typeset -g AIKB_HOOKS_ROOT="$(_aikb_detect_root 2>/dev/null || true)"
typeset -g AIKB_RUNTIME_CLI="${AIKB_HOOKS_ROOT:+$AIKB_HOOKS_ROOT/_tools/memory-pipeline/runtime_cli.py}"
typeset -g AIKB_SESSION_ID="${AIKB_SESSION_ID:-$(hostname 2>/dev/null || echo shell)-$$-$(date +%s)}"
typeset -g AIKB_HOOK_LAST_CMD=""
typeset -g AIKB_HOOK_LAST_START=0
typeset -g AIKB_PROMPT_ENABLE="${AIKB_PROMPT_ENABLE:-0}"
typeset -g AIKB_PROMPT_MODE="${AIKB_PROMPT_MODE:-rprompt}"
typeset -g AIKB_ORIGINAL_PROMPT="${PROMPT:-}"
typeset -g AIKB_ORIGINAL_RPROMPT="${RPROMPT:-}"

_aikb_should_capture_command() {
  local cmd="$1"
  [[ -n "$cmd" ]] || return 1
  [[ "$cmd" =~ '(^|[[:space:]])(git[[:space:]]+(commit|push|pull|merge|rebase)|pytest|pnpm[[:space:]]+test|npm[[:space:]]+test|cargo[[:space:]]+test|go[[:space:]]+test|ansible-playbook|docker[[:space:]]+compose|codex|claude|gemini|aikb)([[:space:]]|$)' ]]
}

_aikb_is_sensitive_command() {
  local cmd="${1:l}"
  [[ "$cmd" == *password* || "$cmd" == *token* || "$cmd" == *secret* || "$cmd" == *api_key* || "$cmd" == *apikey* || "$cmd" == *--session* ]]
}

_aikb_command_label() {
  local -a parts
  parts=("${(z)1}")
  (( ${#parts[@]} == 0 )) && return 1

  case "${parts[1]}" in
    git)
      [[ -n "${parts[2]:-}" ]] && echo "git ${parts[2]}" || echo "git"
      ;;
    pytest|codex|claude|gemini|ansible-playbook)
      echo "${parts[1]} ${parts[2]:-}" | sed 's/[[:space:]]*$//'
      ;;
    npm|pnpm|cargo|go|docker|aikb)
      echo "${parts[1]} ${parts[2]:-} ${parts[3]:-}" | sed 's/[[:space:]]*$//'
      ;;
    *)
      echo "${parts[1]}"
      ;;
  esac
}

_aikb_project_label() {
  local pwd_now="$PWD"
  local home_code="$HOME/code/"
  local home_code_alt="$HOME/Code/"
  if [[ "$pwd_now" == ${home_code}* ]]; then
    echo "${pwd_now#$HOME/code/}"
    return 0
  fi
  if [[ "$pwd_now" == ${home_code_alt}* ]]; then
    echo "${pwd_now#$HOME/Code/}"
    return 0
  fi
  echo "$pwd_now"
}

_aikb_capture_from_shell() {
  local exit_code="$1"
  local duration="$2"
  local raw_cmd="$3"
  local cli="$AIKB_RUNTIME_CLI"

  [[ -n "$cli" && -f "$cli" ]] || return 0
  _aikb_should_capture_command "$raw_cmd" || return 0
  _aikb_is_sensitive_command "$raw_cmd" && return 0

  local label project event_type promote_hint summary
  label="$(_aikb_command_label "$raw_cmd")"
  [[ -n "$label" ]] || return 0
  project="$(_aikb_project_label)"

  if [[ "$exit_code" -eq 0 ]]; then
    event_type="change"
    promote_hint="ignore"
    summary="Command ok (${duration}s): ${label}"
  else
    event_type="blocker"
    promote_hint="candidate"
    summary="Command failed exit=${exit_code} (${duration}s): ${label}"
  fi

  python3 "$cli" capture \
    --agent shell-hook \
    --session-id "$AIKB_SESSION_ID" \
    --type "$event_type" \
    --project "$project" \
    --summary "$summary" \
    --evidence "hook:zsh" \
    --promote-hint "$promote_hint" >/dev/null 2>&1 || true
}

_aikb_preexec() {
  AIKB_HOOK_LAST_CMD="$1"
  AIKB_HOOK_LAST_START="$EPOCHSECONDS"
}

_aikb_precmd() {
  local exit_code=$?
  local cmd="$AIKB_HOOK_LAST_CMD"
  local start="$AIKB_HOOK_LAST_START"
  AIKB_HOOK_LAST_CMD=""
  AIKB_HOOK_LAST_START=0
  [[ -n "$cmd" ]] || return 0
  local duration=0
  if [[ "$start" -gt 0 ]]; then
    duration=$(( EPOCHSECONDS - start ))
  fi
  _aikb_capture_from_shell "$exit_code" "$duration" "$cmd"
}

_aikb_prompt_segment() {
  local cli="$AIKB_RUNTIME_CLI"
  [[ -n "$cli" && -f "$cli" ]] || return 0
  python3 "$cli" prompt 2>/dev/null
}

_aikb_apply_prompt_segment() {
  [[ "$AIKB_PROMPT_ENABLE" == "1" ]] || return 0
  local segment
  segment="$(_aikb_prompt_segment)"
  [[ -n "$segment" ]] || return 0
  if [[ "$AIKB_PROMPT_MODE" == "prompt" ]]; then
    PROMPT="${AIKB_ORIGINAL_PROMPT}"$'\n'"${segment}"$'\n''%# '
  else
    RPROMPT="${segment}"
  fi
}

add-zsh-hook preexec _aikb_preexec
add-zsh-hook precmd _aikb_precmd
add-zsh-hook precmd _aikb_apply_prompt_segment

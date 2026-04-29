#!/usr/bin/env bash
set -euo pipefail

ROOT_PATH=""
ENVIRONMENT_NAME=""
SKIP_PREREQ=0
NON_INTERACTIVE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root-path) ROOT_PATH="$2"; shift 2 ;;
    --environment-name) ENVIRONMENT_NAME="$2"; shift 2 ;;
    --skip-prereq) SKIP_PREREQ=1; shift ;;
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    -h|--help)
      cat <<USAGE
AIKB MSCS Installer Wizard (Bash/WSL)

Usage:
  bash _tools/adapters/mscs/install-wizard.sh [options]

Options:
  --root-path <path>         AIKB root (default: auto-detect)
  --environment-name <name>  Target MSCS/Power Platform environment name
  --skip-prereq              Skip prereq checks
  --non-interactive          Use defaults without prompts
USAGE
      exit 0
      ;;
    *) echo "Unknown argument: $1"; exit 2 ;;
  esac
done

section(){ echo; echo "=== $* ==="; }
step(){ echo " -> $*"; }
warn(){ echo " !! $*"; }
err(){ echo " xx $*"; }

ask(){
  local prompt="$1"; local def="${2:-}"; local v
  if [[ "$NON_INTERACTIVE" -eq 1 ]]; then echo "$def"; return; fi
  if [[ -n "$def" ]]; then
    read -r -p "$prompt [$def]: " v || true
    echo "${v:-$def}"
  else
    read -r -p "$prompt: " v || true
    echo "$v"
  fi
}

valid_url(){
  [[ "$1" =~ ^https?://[^[:space:]]+$ ]]
}

mask_secret(){
  local s="$1"
  local n=${#s}
  if [[ $n -le 0 ]]; then echo "(empty)"; return; fi
  if [[ $n -le 8 ]]; then echo "********"; return; fi
  printf '%*s%s\n' "$((n-4))" '' "${s: -4}" | tr ' ' '*'
}

if [[ -z "$ROOT_PATH" ]]; then
  ROOT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi

ADAPTER_DIR="$ROOT_PATH/_adapters/ms-copilot-studio"
TOOLS_DIR="$ROOT_PATH/_tools/adapters/mscs"
SETUP_SH="$TOOLS_DIR/setup.sh"
PREREQ_PS1="$TOOLS_DIR/prereq-check.ps1"
OPENAPI_PATH="$ADAPTER_DIR/openapi.yaml"
OUT_DIR="$ADAPTER_DIR/onboarding-output"
EFFECTIVE_OPENAPI="$OUT_DIR/openapi.effective.yaml"
PAYLOADS_JSON="$OUT_DIR/test-payloads.json"
GUIDE_TXT="$OUT_DIR/copilot-studio-steps.txt"
SUMMARY_JSON="$OUT_DIR/install-summary.json"
RUNTIME_SH="$OUT_DIR/run-local-adapter.sh"

mkdir -p "$OUT_DIR"

echo "AIKB MS Copilot Studio Installer Wizard (Bash/WSL)"
echo "Root: $ROOT_PATH"

section "Lane Selection"
echo "1) Hosted Adapter (recommended; no local runtime needed)"
echo "2) Self-Hosted Adapter (run AIKB adapter service in WSL/Linux)"
LANE="$(ask "Choose lane number" "1")"
[[ "$LANE" == "1" || "$LANE" == "2" ]] || { warn "Invalid lane '$LANE', using 1"; LANE="1"; }

FAILS=0
WARNS=0
PREREQ_REPORT="$OUT_DIR/mscs-prereq-report.json"

if [[ "$SKIP_PREREQ" -eq 0 ]]; then
  section "Prerequisite Check (WSL/Linux)"
  # WSL/Linux-focused checks
  PY=""
  for c in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
  done
  if [[ -z "$PY" ]]; then
    err "Python 3.10+ not found"
    FAILS=$((FAILS+1))
  else
    step "Python found: $($PY --version 2>/dev/null || true)"
  fi

  if [[ ! -f "$SETUP_SH" ]]; then
    err "Missing setup script: $SETUP_SH"
    FAILS=$((FAILS+1))
  fi

  if [[ ! -f "$OPENAPI_PATH" ]]; then
    warn "OpenAPI scaffold missing (will be created by setup.sh)"
    WARNS=$((WARNS+1))
  fi

  # Try to run PowerShell prereq checker if pwsh available (optional)
  if command -v pwsh >/dev/null 2>&1 && [[ -f "$PREREQ_PS1" ]]; then
    step "Running supplemental Power Platform prereq checker via pwsh"
    set +e
    if [[ -n "$ENVIRONMENT_NAME" ]]; then
      pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$PREREQ_PS1" -EnvironmentName "$ENVIRONMENT_NAME" -OutputPath "$PREREQ_REPORT"
    else
      pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$PREREQ_PS1" -OutputPath "$PREREQ_REPORT"
    fi
    rc=$?
    set -e
    if [[ $rc -ne 0 ]]; then warn "Power Platform prereq checker returned code $rc"; fi
  else
    warn "pwsh unavailable; skipping Power Platform module/auth checks."
    warn "Run prereq-check.ps1 from Windows PowerShell for full tenant permission diagnostics."
    WARNS=$((WARNS+1))
  fi

  echo "Prereq summary: fails=$FAILS warns=$WARNS"
  if [[ $FAILS -gt 0 && "$NON_INTERACTIVE" -eq 0 ]]; then
    c="$(ask "Blocking issues found. Continue anyway? (y/N)" "N")"
    [[ "${c,,}" == "y" ]] || exit 2
  elif [[ $FAILS -gt 0 ]]; then
    exit 2
  fi
fi

section "Adapter Scaffold"
[[ -f "$SETUP_SH" ]] || { err "Missing setup script: $SETUP_SH"; exit 2; }
step "Running scaffold setup"
bash "$SETUP_SH"
[[ -f "$OPENAPI_PATH" ]] || { err "OpenAPI not found after scaffold: $OPENAPI_PATH"; exit 2; }

section "Connection/Auth Setup"
AUTH_MODE="$(ask "Auth mode (api_key/none)" "api_key")"
[[ "$AUTH_MODE" == "api_key" || "$AUTH_MODE" == "none" ]] || { warn "Invalid auth mode '$AUTH_MODE', using api_key"; AUTH_MODE="api_key"; }

API_KEY=""
if [[ "$AUTH_MODE" == "api_key" ]]; then
  echo "API key guidance:"
  echo "- Dev pilot: random key, share securely"
  echo "- Prod: store in secret manager, rotate"
  API_KEY="$(ask "Enter API key (blank to generate)" "")"
  if [[ -z "$API_KEY" ]]; then
    API_KEY="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)"
    step "Generated random API key"
  fi
fi

DEFAULT_BASE="https://your-adapter-host.example.com"
[[ "$LANE" == "2" ]] && DEFAULT_BASE="http://127.0.0.1:8787"
ADAPTER_BASE_URL="$(ask "Adapter base URL" "$DEFAULT_BASE")"
if ! valid_url "$ADAPTER_BASE_URL"; then
  warn "Invalid URL '$ADAPTER_BASE_URL', using '$DEFAULT_BASE'"
  ADAPTER_BASE_URL="$DEFAULT_BASE"
fi

TENANT_ID="$(ask "Default tenant_id" "example-tenant")"
PROJECT_ID="$(ask "Default project_id" "example-project")"

cat > "$ADAPTER_DIR/.env.local" <<ENV
AIKB_AUTH_MODE=$AUTH_MODE
AIKB_API_KEY=$API_KEY
AIKB_ADAPTER_BASE_URL=$ADAPTER_BASE_URL
AIKB_TENANT_ID=$TENANT_ID
AIKB_PROJECT_ID=$PROJECT_ID
ENV
step "Wrote: $ADAPTER_DIR/.env.local"

section "OpenAPI Preparation"
sed "s|https://your-adapter-host.example.com|$ADAPTER_BASE_URL|g" "$OPENAPI_PATH" > "$EFFECTIVE_OPENAPI"
step "Wrote: $EFFECTIVE_OPENAPI"

section "Generate Test Bundle"
cat > "$PAYLOADS_JSON" <<JSON
{
  "remember": {
    "tenant_id": "$TENANT_ID",
    "project_id": "$PROJECT_ID",
    "agent_id": "mscs-agent-01",
    "user_id": "user@example.com",
    "text": "User prefers email follow-up after 3 PM ET.",
    "tags": ["preference", "pilot"],
    "source": "copilot_studio",
    "pii_level": "normal"
  },
  "recall": {
    "tenant_id": "$TENANT_ID",
    "project_id": "$PROJECT_ID",
    "query": "preferred contact channel and time",
    "limit": 5
  },
  "context_pack": {
    "tenant_id": "$TENANT_ID",
    "project_id": "$PROJECT_ID",
    "query": "summarize known communication preferences",
    "limit": 5
  }
}
JSON
step "Wrote: $PAYLOADS_JSON"

cat > "$GUIDE_TXT" <<TXT
AIKB MSCS Connector Guided Steps
================================
1) Open Copilot Studio / Power Platform Custom Connectors.
2) Create connector from OpenAPI file:
   $EFFECTIVE_OPENAPI
3) Security:
   - auth_mode=$AUTH_MODE
   - if api_key: header name is x-api-key
4) Create a Connection for the connector.
5) Add actions:
   - POST /copilot/remember
   - POST /copilot/recall
   - POST /copilot/context-pack
6) Wire behavior:
   - Before answering: context-pack or recall
   - After answering: remember
7) Use payloads:
   $PAYLOADS_JSON
8) Verify base URL and API key if calls fail.
TXT
step "Wrote: $GUIDE_TXT"

RUNTIME_OK=0
if [[ "$LANE" == "2" ]]; then
  section "Self-Hosted Runtime Checks"
  VENV_PY="$ROOT_PATH/_tools/aikb-search/.venv/bin/python"
  if [[ -x "$VENV_PY" ]]; then
    step "Found venv python: $VENV_PY"
    RUNTIME_OK=1
  else
    warn "Missing venv python: $VENV_PY"
    warn "Run: bash _tools/aikb-search/setup.sh"
  fi

  cat > "$RUNTIME_SH" <<SH
#!/usr/bin/env bash
set -euo pipefail
export AIKB_AUTH_MODE="$AUTH_MODE"
export AIKB_API_KEY="$API_KEY"
export AIKB_TENANT_ID="$TENANT_ID"
export AIKB_PROJECT_ID="$PROJECT_ID"
"$VENV_PY" "$ROOT_PATH/_adapters/ms-copilot-studio/server.py"
SH
  chmod +x "$RUNTIME_SH"
  step "Wrote: $RUNTIME_SH"
fi

section "Permission Requests (if blocked)"
echo "- Copilot Studio maker rights"
echo "- Custom connector create/edit rights"
echo "- Connector connection creation rights"
echo "- DLP approval for custom connector"
echo "- Entra app registration/consent help (if OAuth)"

cat > "$SUMMARY_JSON" <<JSON
{
  "lane": "$( [[ "$LANE" == "1" ]] && echo hosted || echo self_hosted )",
  "environment_name": "$ENVIRONMENT_NAME",
  "auth_mode": "$AUTH_MODE",
  "api_key_preview": "$(mask_secret "$API_KEY")",
  "adapter_base_url": "$ADAPTER_BASE_URL",
  "tenant_id": "$TENANT_ID",
  "project_id": "$PROJECT_ID",
  "prereq_fails": $FAILS,
  "prereq_warns": $WARNS,
  "outputs": {
    "effective_openapi": "$EFFECTIVE_OPENAPI",
    "test_payloads": "$PAYLOADS_JSON",
    "guide": "$GUIDE_TXT",
    "summary": "$SUMMARY_JSON",
    "runtime_launcher": "$( [[ "$LANE" == "2" ]] && echo "$RUNTIME_SH" || echo "" )"
  }
}
JSON

section "Complete"
echo "Output folder: $OUT_DIR"
echo "Summary: $SUMMARY_JSON"
[[ "$LANE" == "2" && $RUNTIME_OK -eq 0 ]] && warn "Self-hosted selected, but runtime prereqs are incomplete."
echo "Next: follow copilot-studio-steps.txt"

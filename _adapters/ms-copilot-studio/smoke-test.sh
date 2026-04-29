#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AIKB_ADAPTER_BASE_URL:-http://127.0.0.1:8787}"
API_KEY="${AIKB_API_KEY:-}"

hdr=("-H" "Content-Type: application/json")
if [[ -n "$API_KEY" ]]; then
  hdr+=("-H" "x-api-key: $API_KEY")
fi

echo "[1/4] health"
curl -s "$BASE_URL/health" | sed 's/.*/&\n/'

echo "[2/4] remember"
curl -s "${hdr[@]}" -X POST "$BASE_URL/copilot/remember" -d '{
  "tenant_id":"demo-tenant",
  "project_id":"demo-project",
  "agent_id":"mscs-demo",
  "user_id":"user-1",
  "text":"User prefers email updates after 3 PM ET.",
  "tags":["preference","onboarding"],
  "source":"copilot_studio",
  "pii_level":"normal"
}' | sed 's/.*/&\n/'

echo "[3/4] recall"
curl -s "${hdr[@]}" -X POST "$BASE_URL/copilot/recall" -d '{
  "tenant_id":"demo-tenant",
  "project_id":"demo-project",
  "query":"preferred contact channel and time",
  "limit":5
}' | sed 's/.*/&\n/'

echo "[4/4] context-pack"
curl -s "${hdr[@]}" -X POST "$BASE_URL/copilot/context-pack" -d '{
  "tenant_id":"demo-tenant",
  "project_id":"demo-project",
  "query":"summarize known communication preferences",
  "limit":5
}' | sed 's/.*/&\n/'

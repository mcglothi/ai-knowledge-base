#!/usr/bin/env bash
set -euo pipefail
CONF="$HOME/.codex/config.toml"
URL_DEFAULT="https://mcp.your-homelab.example.com/mcp"

if [[ ! -f "$CONF" ]]; then
  echo "ERROR: missing $CONF"
  exit 2
fi

AUTH=$(python3 - <<'PY'
import re
from pathlib import Path
p=Path.home()/'.codex'/'config.toml'
s=p.read_text() if p.exists() else ''
m=re.search(r'--auth",\s*"([^"]+)"', s)
print(m.group(1) if m else '')
PY
)

URL=$(python3 - <<'PY'
import re
from pathlib import Path
p=Path.home()/'.codex'/'config.toml'
s=p.read_text() if p.exists() else ''
m=re.search(r'--url",\s*"([^"]+)"', s)
print(m.group(1) if m else 'https://mcp.your-homelab.example.com/mcp')
PY
)

if [[ -z "$AUTH" ]]; then
  echo "WARN: no --auth found in codex homelab config"
fi

probe() {
  local url="$1"
  local code ctype loc
  code=$(curl -sS -L -o /tmp/codex_homelab_body -D /tmp/codex_homelab_hdr \
    -H "Accept: text/event-stream" \
    ${AUTH:+-H "Authorization: Basic $AUTH"} \
    "$url" -m 15 -w '%{http_code}' || true)
  ctype=$(grep -i '^content-type:' /tmp/codex_homelab_hdr | tail -1 | tr -d '\r' || true)
  loc=$(grep -i '^location:' /tmp/codex_homelab_hdr | tail -1 | tr -d '\r' || true)
  body=$(head -c 120 /tmp/codex_homelab_body | tr '\n' ' ')
  echo "URL: $url"
  echo "HTTP: $code"
  echo "CTYPE: ${ctype:-<none>}"
  [[ -n "$loc" ]] && echo "LOCATION: $loc"
  echo "BODY: $body"
  echo
}

echo "[codex-homelab] probing current configured URL"
probe "$URL"

echo "[codex-homelab] probing common alternatives"
probe "https://mcp.your-homelab.example.com/sse"
probe "https://mcp.your-homelab.example.com/mcp"
probe "https://mcp.your-homelab.example.com/"

echo "[codex-homelab] NOTE: readiness requires final content-type text/event-stream without HTML login redirect."

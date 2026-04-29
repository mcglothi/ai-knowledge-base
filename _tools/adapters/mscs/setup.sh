#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ADAPTER_DIR="$ROOT_DIR/_adapters/ms-copilot-studio"
OPENAPI_PATH="$ADAPTER_DIR/openapi.yaml"
README_PATH="$ADAPTER_DIR/README.md"
ENV_EXAMPLE="$ADAPTER_DIR/.env.example"

mkdir -p "$ADAPTER_DIR"

if [[ ! -f "$README_PATH" ]]; then
  cat > "$README_PATH" <<'MD'
# AIKB Adapter: Microsoft Copilot Studio (Scaffold)

Status: scaffold

This directory is reserved for the Microsoft Copilot Studio adapter.

Planned facade endpoints:
- POST /copilot/remember
- POST /copilot/recall
- POST /copilot/context-pack
- POST /copilot/feedback (optional)

Notes:
- Keep translation layer thin (map directly to AIKB core primitives)
- Keep enterprise controls reusable where possible (tenant scope, PII hooks, audit)
MD
fi

if [[ ! -f "$OPENAPI_PATH" ]]; then
  cat > "$OPENAPI_PATH" <<'YAML'
openapi: 3.0.3
info:
  title: AIKB Copilot Studio Adapter (Scaffold)
  version: 0.1.0
  description: >
    Scaffold spec for Microsoft Copilot Studio custom connector integration.
servers:
  - url: https://example-aikb-adapter.local
paths:
  /copilot/remember:
    post:
      summary: Remember a memory event
      responses:
        '200':
          description: OK
  /copilot/recall:
    post:
      summary: Recall relevant memory
      responses:
        '200':
          description: OK
  /copilot/context-pack:
    post:
      summary: Build compact prompt context from memory
      responses:
        '200':
          description: OK
YAML
fi

if [[ ! -f "$ENV_EXAMPLE" ]]; then
  cat > "$ENV_EXAMPLE" <<'ENV'
# Adapter environment (example)
AIKB_ADAPTER_BASE_URL=https://example-aikb-adapter.local
AIKB_AUTH_MODE=api_key
AIKB_TENANT_ID=example-tenant
AIKB_PROJECT_ID=example-project
ENV
fi

echo "✅ MS Copilot Studio adapter scaffold ready:"
echo "   $ADAPTER_DIR"
echo ""
echo "Next steps:"
echo "1) Implement thin endpoint handlers (remember/recall/context-pack)"
echo "2) Replace example server URL in openapi.yaml"
echo "3) Import openapi.yaml into Copilot Studio custom connector"
echo "4) Run smoke test: remember -> recall"

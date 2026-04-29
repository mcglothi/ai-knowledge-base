# AIKB Adapter: Microsoft Copilot Studio

Runnable MVP adapter for Microsoft Copilot Studio custom connectors.

## What this provides
- HTTP endpoints: `/copilot/remember`, `/copilot/recall`, `/copilot/context-pack`
- API-key auth option for dev pilots
- OpenAPI spec for connector import
- Thin mapping to AIKB core primitives (runtime events + search index)

## Run locally
From AIKB root:

```bash
_tools/aikb-search/.venv/bin/python _adapters/ms-copilot-studio/server.py
```

Default:
- URL: `http://127.0.0.1:8787`
- Auth: `none`

### Enable API key auth (recommended for connector testing)
```bash
export AIKB_AUTH_MODE=api_key
export AIKB_API_KEY='change-me'
_tools/aikb-search/.venv/bin/python _adapters/ms-copilot-studio/server.py
```

### Windows PowerShell
```powershell
$env:AIKB_AUTH_MODE = "api_key"
$env:AIKB_API_KEY = "change-me"
.\_tools\aikb-search\.venv\Scripts\python.exe .\_adapters\ms-copilot-studio\server.py
```

## Connector import
- Import: `_adapters/ms-copilot-studio/openapi.yaml`
- Set server URL to your hosted adapter URL
- Configure auth header `x-api-key` (if using API key mode)

## Quick smoke test
```bash
bash _adapters/ms-copilot-studio/smoke-test.sh
```

## Notes
- This is MVP quality for pilot/testing.
- Production hardening should add OAuth/Entra flow, stronger tenancy/PII controls, and centralized audit.

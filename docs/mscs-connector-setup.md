# Microsoft Copilot Studio Connector Setup
**Last Updated:** 2026-04-29

Use this guide after standard AIKB setup when you want to connect **Microsoft Copilot Studio (MSCS)** to AIKB memory/search.

> Important: This is an **optional addon lane**. Do the normal AIKB install first.
> For Windows-first MSCS teams, you can use the connector lane **without WSL** if your adapter is hosted remotely.

## Scope
This setup covers:
- Connector-friendly AIKB facade planning (`remember`, `recall`, `context-pack`)
- OpenAPI import workflow for Copilot Studio custom connectors
- Dev validation path for first successful recall

This setup does **not** replace existing GitHub Copilot CLI support.

## Prerequisites
1. AIKB installed normally (see `docs/getting-started.md`)
2. Access to a Microsoft tenant with Copilot Studio + connector permissions
3. A reachable adapter endpoint URL (dev/staging/prod)
4. Auth plan decided (API key for dev, OAuth/Entra for enterprise)

## Windows-first install lanes
### Lane A (recommended for most MSCS users): **No WSL required**
Use this when your AIKB adapter is hosted (Azure/App Service/Container/etc.) and Windows users only need Copilot Studio + connector configuration.

### Lane B (optional advanced): **WSL/local AIKB runtime**
Use this when users need to run local AIKB tools/runtime on Windows. Follow `docs/windows-wsl.md` first.

## Product Naming (avoid confusion)
- **Microsoft Copilot Studio** = enterprise agent orchestration platform
- **GitHub Copilot CLI** = developer CLI agent

Treat these as separate integrations and docs lanes.

## Recommended Onboarding Path

### Step 1 — Scaffold adapter artifacts (if self-hosting)
From AIKB root:

**macOS/Linux/WSL**
```bash
bash _tools/adapters/mscs/setup.sh
```

**Windows PowerShell (no WSL required)**
```powershell
powershell -ExecutionPolicy Bypass -File .\_tools\adapters\mscs\setup.ps1
```

This scaffolds local adapter placeholders and prints next actions. If your org already provides a hosted adapter + OpenAPI spec, you can skip this scaffold step.

### Step 2 — Import OpenAPI in Copilot Studio
1. Go to Copilot Studio / Power Platform custom connectors
2. Create connector from OpenAPI file/URL
3. Define auth (temporary API key in dev, OAuth in enterprise)
4. Create actions:
   - `remember`
   - `recall`
   - `context-pack`

### Step 3 — Wire actions into your Copilot
- Before final response: call `context-pack` or `recall`
- After response (or decision boundary): call `remember`
- Handle connector failure gracefully (continue without memory + log warning)

### Step 4 — Smoke test
Run one end-to-end flow:
1. Ask Copilot to remember a preference
2. Ask a follow-up requiring recall
3. Validate AIKB returns the saved memory

Expected: successful `remember` + `recall` with tenant/project scope.

## Suggested API Surface (connector facade)
- `POST /copilot/remember`
- `POST /copilot/recall`
- `POST /copilot/context-pack`
- Optional: `POST /copilot/feedback`

Keep this layer thin: map directly to AIKB core primitives.

## Governance Checklist (enterprise)
- [ ] tenant/project/agent namespace in every request
- [ ] PII redaction hook before persistent write
- [ ] retention policy by memory class
- [ ] audit trail for read/write calls
- [ ] explicit disambiguation in docs/UI labels (MSCS vs GitHub Copilot)

## Troubleshooting
- **Connector imports but actions fail** → verify endpoint URL, auth headers, and schema shapes
- **Recall returns empty** → check scoping filters (`tenant_id`, `project_id`) and search query quality
- **Inconsistent behavior** → inspect adapter logs for request translation + latency
- **Security review blocks rollout** → start with dev tenant + mock auth path and staged controls

## Related Docs
- `docs/getting-started.md`
- `docs/windows-wsl.md`
- `docs/mcp-setup.md`
- `docs/agent-im.md`

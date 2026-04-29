Param(
  [string]$RootPath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RootPath)) {
  $RootPath = (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
}

$adapterDir = Join-Path $RootPath "_adapters/ms-copilot-studio"
$openapiPath = Join-Path $adapterDir "openapi.yaml"
$readmePath = Join-Path $adapterDir "README.md"
$envExamplePath = Join-Path $adapterDir ".env.example"

New-Item -ItemType Directory -Path $adapterDir -Force | Out-Null

if (-not (Test-Path $readmePath)) {
@'
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
'@ | Set-Content -Path $readmePath -Encoding UTF8
}

if (-not (Test-Path $openapiPath)) {
@'
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
'@ | Set-Content -Path $openapiPath -Encoding UTF8
}

if (-not (Test-Path $envExamplePath)) {
@'
# Adapter environment (example)
AIKB_ADAPTER_BASE_URL=https://example-aikb-adapter.local
AIKB_AUTH_MODE=api_key
AIKB_TENANT_ID=example-tenant
AIKB_PROJECT_ID=example-project
'@ | Set-Content -Path $envExamplePath -Encoding UTF8
}

Write-Host "✅ MS Copilot Studio adapter scaffold ready:" -ForegroundColor Green
Write-Host "   $adapterDir"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1) Implement thin endpoint handlers (remember/recall/context-pack)"
Write-Host "2) Replace example server URL in openapi.yaml"
Write-Host "3) Import openapi.yaml into Copilot Studio custom connector"
Write-Host "4) Run smoke test: remember -> recall"

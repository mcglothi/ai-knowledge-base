Param(
  [string]$RootPath = "",
  [string]$EnvironmentName = "",
  [switch]$SkipPrereq,
  [switch]$NonInteractive
)

$ErrorActionPreference = "Continue"

function Write-Section($text) {
  Write-Host ""
  Write-Host "=== $text ===" -ForegroundColor Cyan
}

function Write-Step($text) {
  Write-Host " -> $text" -ForegroundColor Gray
}

function Write-Warn($text) {
  Write-Host " !! $text" -ForegroundColor Yellow
}

function Write-Err($text) {
  Write-Host " xx $text" -ForegroundColor Red
}

function Ask($prompt, $default="") {
  if ($NonInteractive) { return $default }
  if ([string]::IsNullOrWhiteSpace($default)) {
    return Read-Host $prompt
  }
  $v = Read-Host "$prompt [$default]"
  if ([string]::IsNullOrWhiteSpace($v)) { return $default }
  return $v
}

function Ask-Choice($prompt, [string[]]$valid, $default) {
  $v = Ask $prompt $default
  if ($valid -contains $v) { return $v }
  Write-Warn "Invalid choice '$v'. Using '$default'."
  return $default
}

function Is-ValidUrl($url) {
  try {
    $u = [System.Uri]$url
    return ($u.Scheme -in @('http','https')) -and -not [string]::IsNullOrWhiteSpace($u.Host)
  } catch {
    return $false
  }
}

function Ensure-Dir($path) {
  New-Item -ItemType Directory -Path $path -Force | Out-Null
}

function Mask-Secret($s) {
  if ([string]::IsNullOrWhiteSpace($s)) { return "(empty)" }
  if ($s.Length -le 8) { return "********" }
  return ("*" * ($s.Length - 4)) + $s.Substring($s.Length - 4)
}

if ([string]::IsNullOrWhiteSpace($RootPath)) {
  $RootPath = (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
}

$adapterDir = Join-Path $RootPath "_adapters/ms-copilot-studio"
$toolsDir = Join-Path $RootPath "_tools/adapters/mscs"
$prereqScript = Join-Path $toolsDir "prereq-check.ps1"
$setupScript = Join-Path $toolsDir "setup.ps1"
$openapiPath = Join-Path $adapterDir "openapi.yaml"
$outDir = Join-Path $adapterDir "onboarding-output"
$effectiveOpenApi = Join-Path $outDir "openapi.effective.yaml"
$payloadsPath = Join-Path $outDir "test-payloads.json"
$guidePath = Join-Path $outDir "copilot-studio-steps.txt"
$summaryPath = Join-Path $outDir "install-summary.json"
$runtimeLauncherPath = Join-Path $outDir "run-local-adapter.ps1"

Ensure-Dir $outDir

Write-Host "AIKB MS Copilot Studio Installer Wizard" -ForegroundColor Green
Write-Host "Root: $RootPath"

Write-Section "Lane Selection"
Write-Host "1) Hosted Adapter (recommended, no local runtime needed)"
Write-Host "2) Self-Hosted Adapter (run AIKB adapter service locally or on your infra)"
$lane = Ask-Choice "Choose lane number" @("1","2") "1"

if ($lane -eq "1") {
  Write-Warn "You selected Hosted (no WSL/local runtime)."
  Write-Host "What you will NOT get without WSL/local runtime:" -ForegroundColor Yellow
  Write-Host "- Local AIKB search index build/rebuild (_tools/aikb-search)"
  Write-Host "- Running the adapter service locally for offline/dev testing"
  Write-Host "- Local memory/search pipeline debugging on this machine"
  Write-Host "You can still use MS Copilot Studio with a hosted adapter endpoint." -ForegroundColor Yellow
}

# ---------------- Prereq ----------------
$failsCount = 0
$warnsCount = 0
$reportPath = Join-Path $outDir "mscs-prereq-report.json"

if (-not $SkipPrereq) {
  Write-Section "Prerequisite Check"
  if (-not (Test-Path $prereqScript)) {
    Write-Err "Prereq checker not found: $prereqScript"
    exit 2
  }

  $args = @("-ExecutionPolicy","Bypass","-File",$prereqScript,"-OutputPath",$reportPath)
  if (-not [string]::IsNullOrWhiteSpace($EnvironmentName)) {
    $args += @("-EnvironmentName", $EnvironmentName)
  }

  Write-Step "Running prereq checker..."
  & powershell @args
  $prereqExit = $LASTEXITCODE

  if (Test-Path $reportPath) {
    try {
      $report = Get-Content $reportPath -Raw | ConvertFrom-Json
      $fails = @($report.results | Where-Object { $_.status -eq 'fail' })
      $warns = @($report.results | Where-Object { $_.status -eq 'warn' })
      $failsCount = $fails.Count
      $warnsCount = $warns.Count

      Write-Host "Prereq summary: fails=$failsCount, warns=$warnsCount" -ForegroundColor Yellow

      if ($failsCount -gt 0) {
        Write-Err "Blocking prereq failures detected."
        Write-Host "Review: $reportPath"
        if (-not $NonInteractive) {
          $cont = Ask-Choice "Continue anyway? (y/N)" @("y","Y","n","N") "N"
          if ($cont.ToLower() -ne "y") { exit 2 }
        }
      }
    } catch {
      Write-Warn "Could not parse prereq report JSON: $reportPath"
    }
  } else {
    Write-Warn "Prereq report missing: $reportPath"
  }

  if ($prereqExit -ne 0) {
    Write-Warn "Prereq checker exit code: $prereqExit"
  }
}

# ---------------- Scaffold ----------------
Write-Section "Adapter Scaffold"
if (-not (Test-Path $setupScript)) {
  Write-Err "Setup script not found: $setupScript"
  exit 2
}
Write-Step "Scaffolding adapter files..."
& powershell -ExecutionPolicy Bypass -File $setupScript -RootPath $RootPath | Out-Host

if (-not (Test-Path $openapiPath)) {
  Write-Err "Expected OpenAPI not found at $openapiPath"
  exit 2
}

# ---------------- Auth/Input ----------------
Write-Section "Connection/Auth Setup"
$authMode = Ask-Choice "Auth mode for connector (api_key/none)" @("api_key","none") "api_key"

$apiKey = ""
if ($authMode -eq "api_key") {
  Write-Host "API key guidance:" -ForegroundColor Yellow
  Write-Host "- Dev pilot: generate random key, share via secure channel/vault."
  Write-Host "- Production: store in secret manager (e.g., Key Vault), rotate regularly."

  $apiKey = Ask "Enter API key to configure (blank = generate)" ""
  if ([string]::IsNullOrWhiteSpace($apiKey)) {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $apiKey = [Convert]::ToBase64String($bytes)
    Write-Step "Generated random API key"
  }
}

$defaultBase = if ($lane -eq "2") { "http://127.0.0.1:8787" } else { "https://your-adapter-host.example.com" }
$adapterBaseUrl = Ask "Adapter base URL (what Copilot Studio calls)" $defaultBase
if (-not (Is-ValidUrl $adapterBaseUrl)) {
  Write-Warn "Base URL '$adapterBaseUrl' is invalid. Falling back to '$defaultBase'."
  $adapterBaseUrl = $defaultBase
}

$tenantId = Ask "Default tenant_id" "example-tenant"
$projectId = Ask "Default project_id" "example-project"

# Persist runtime env (local convenience)
$envFile = Join-Path $adapterDir ".env.local"
@"
AIKB_AUTH_MODE=$authMode
AIKB_API_KEY=$apiKey
AIKB_ADAPTER_BASE_URL=$adapterBaseUrl
AIKB_TENANT_ID=$tenantId
AIKB_PROJECT_ID=$projectId
"@ | Set-Content -Path $envFile -Encoding UTF8
Write-Step "Wrote runtime env template: $envFile"

# ---------------- OpenAPI effective ----------------
Write-Section "OpenAPI Preparation"
$yaml = Get-Content $openapiPath -Raw
$yaml = $yaml.Replace("https://your-adapter-host.example.com", $adapterBaseUrl)
$yaml | Set-Content -Path $effectiveOpenApi -Encoding UTF8
Write-Step "Wrote effective OpenAPI: $effectiveOpenApi"

# ---------------- Payloads + guide ----------------
Write-Section "Generate Test Bundle"
$payloads = [PSCustomObject]@{
  remember = [PSCustomObject]@{
    tenant_id = $tenantId
    project_id = $projectId
    agent_id = "mscs-agent-01"
    user_id = "user@example.com"
    text = "User prefers email follow-up after 3 PM ET."
    tags = @("preference","pilot")
    source = "copilot_studio"
    pii_level = "normal"
  }
  recall = [PSCustomObject]@{
    tenant_id = $tenantId
    project_id = $projectId
    query = "preferred contact channel and time"
    limit = 5
  }
  context_pack = [PSCustomObject]@{
    tenant_id = $tenantId
    project_id = $projectId
    query = "summarize known communication preferences"
    limit = 5
  }
}
$payloads | ConvertTo-Json -Depth 8 | Set-Content -Path $payloadsPath -Encoding UTF8
Write-Step "Wrote test payloads: $payloadsPath"

@"
AIKB MSCS Connector Guided Steps
================================
1) Open Copilot Studio / Power Platform Custom Connectors.
2) Create connector from OpenAPI file:
   $effectiveOpenApi
3) Security:
   - auth_mode=$authMode
   - if api_key: header name is x-api-key
4) Create a Connection for the connector.
5) In Copilot Studio, add actions:
   - POST /copilot/remember
   - POST /copilot/recall
   - POST /copilot/context-pack
6) Wire behavior:
   - Before answering: context-pack or recall
   - After answering: remember
7) Use payloads from:
   $payloadsPath
8) If calls fail, verify:
   - base URL ($adapterBaseUrl)
   - API key value in connector connection
   - network reachability from tenant environment
"@ | Set-Content -Path $guidePath -Encoding UTF8
Write-Step "Wrote guided steps: $guidePath"

# ---------------- Self-host lane helpers ----------------
$localRuntimeOk = $false
if ($lane -eq "2") {
  Write-Section "Self-Hosted Runtime Checks"
  $venvPython = Join-Path $RootPath "_tools/aikb-search/.venv/Scripts/python.exe"
  if (Test-Path $venvPython) {
    $localRuntimeOk = $true
    Write-Step "Found AIKB venv Python: $venvPython"
  } else {
    Write-Warn "AIKB venv Python not found at: $venvPython"
    Write-Host "Run this first:" -ForegroundColor Yellow
    Write-Host "  bash _tools/aikb-search/setup.sh"
  }

  @"
`$env:AIKB_AUTH_MODE = "$authMode"
`$env:AIKB_API_KEY = "$apiKey"
`$env:AIKB_TENANT_ID = "$tenantId"
`$env:AIKB_PROJECT_ID = "$projectId"
# optional:
# `$env:AIKB_ADAPTER_HOST = "127.0.0.1"
# `$env:AIKB_ADAPTER_PORT = "8787"

$venvPython .\_adapters\ms-copilot-studio\server.py
"@ | Set-Content -Path $runtimeLauncherPath -Encoding UTF8
  Write-Step "Wrote local runtime launcher: $runtimeLauncherPath"
}

# ---------------- Summary ----------------
Write-Section "Permission Requests (if blocked)"
Write-Host "Request these if setup is blocked:" -ForegroundColor Yellow
Write-Host "- Copilot Studio maker rights in target environment"
Write-Host "- Power Platform custom connector create/edit rights"
Write-Host "- Permission to create connector connections"
Write-Host "- DLP approval for custom connector usage"
Write-Host "- (If OAuth) Entra app registration/consent support"

$summary = [PSCustomObject]@{
  generated_utc = (Get-Date).ToUniversalTime().ToString("s") + "Z"
  lane = if ($lane -eq "1") { "hosted" } else { "self_hosted" }
  environment_name = $EnvironmentName
  auth_mode = $authMode
  api_key_preview = (Mask-Secret $apiKey)
  adapter_base_url = $adapterBaseUrl
  tenant_id = $tenantId
  project_id = $projectId
  prereq_fails = $failsCount
  prereq_warns = $warnsCount
  outputs = [PSCustomObject]@{
    prereq_report = $reportPath
    effective_openapi = $effectiveOpenApi
    test_payloads = $payloadsPath
    guide = $guidePath
    env_local = $envFile
    runtime_launcher = if ($lane -eq "2") { $runtimeLauncherPath } else { "" }
  }
}
$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $summaryPath -Encoding UTF8

Write-Section "Complete"
Write-Host "Wizard output folder: $outDir" -ForegroundColor Green
Write-Host "Install summary: $summaryPath" -ForegroundColor Green
if ($lane -eq "2" -and -not $localRuntimeOk) {
  Write-Warn "Self-hosted lane selected but local runtime prerequisites are incomplete."
}
Write-Host "Next: follow copilot-studio-steps.txt and run endpoint tests." -ForegroundColor Green

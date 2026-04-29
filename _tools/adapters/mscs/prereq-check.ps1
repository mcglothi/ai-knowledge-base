Param(
  [string]$EnvironmentName = "",
  [string]$OutputPath = ".\\mscs-prereq-report.json"
)

$ErrorActionPreference = "Continue"

function Add-Result {
  param(
    [string]$Check,
    [string]$Status,
    [string]$Details,
    [string]$RequestIfMissing = ""
  )
  $script:Results += [PSCustomObject]@{
    check = $Check
    status = $Status   # pass | warn | fail | info
    details = $Details
    request_if_missing = $RequestIfMissing
  }
}

$Results = @()

Write-Host "== AIKB MS Copilot Studio Prereq Check ==" -ForegroundColor Cyan
Write-Host "This script performs best-effort checks for MSCS + Power Platform access."
Write-Host ""

# 1) PowerShell version
if ($PSVersionTable.PSVersion.Major -ge 7 -or $PSVersionTable.PSVersion.Major -ge 5) {
  Add-Result -Check "PowerShell available" -Status "pass" -Details "PowerShell $($PSVersionTable.PSVersion)"
} else {
  Add-Result -Check "PowerShell available" -Status "fail" -Details "Unsupported PowerShell version" -RequestIfMissing "Install PowerShell 7+"
}

# 2) Required modules
$adminModule = Get-Module -ListAvailable -Name Microsoft.PowerApps.Administration.PowerShell
$userModule  = Get-Module -ListAvailable -Name Microsoft.PowerApps.PowerShell

if ($adminModule) {
  Add-Result -Check "Module: Microsoft.PowerApps.Administration.PowerShell" -Status "pass" -Details "Installed"
} else {
  Add-Result -Check "Module: Microsoft.PowerApps.Administration.PowerShell" -Status "warn" -Details "Not installed" -RequestIfMissing "Install-Module Microsoft.PowerApps.Administration.PowerShell -Scope CurrentUser"
}

if ($userModule) {
  Add-Result -Check "Module: Microsoft.PowerApps.PowerShell" -Status "pass" -Details "Installed"
} else {
  Add-Result -Check "Module: Microsoft.PowerApps.PowerShell" -Status "warn" -Details "Not installed" -RequestIfMissing "Install-Module Microsoft.PowerApps.PowerShell -Scope CurrentUser"
}

# 3) Try importing modules
$importOk = $true
try {
  Import-Module Microsoft.PowerApps.Administration.PowerShell -ErrorAction Stop
  Import-Module Microsoft.PowerApps.PowerShell -ErrorAction Stop
  Add-Result -Check "Import Power Platform modules" -Status "pass" -Details "Modules imported successfully"
} catch {
  $importOk = $false
  Add-Result -Check "Import Power Platform modules" -Status "fail" -Details $_.Exception.Message -RequestIfMissing "Install/import the two Power Platform modules"
}

$envs = @()
$selectedEnv = $null

if ($importOk) {
  # 4) Authentication
  $authOk = $true
  try {
    # Prompts interactive login if needed
    Add-PowerAppsAccount | Out-Null
    Add-Result -Check "Power Platform authentication" -Status "pass" -Details "Authenticated successfully"
  } catch {
    $authOk = $false
    Add-Result -Check "Power Platform authentication" -Status "fail" -Details $_.Exception.Message -RequestIfMissing "Sign in with a licensed account that can access target environment"
  }

  if ($authOk) {
    # 5) Environment visibility
    try {
      $envs = @(Get-AdminPowerAppEnvironment)
      if ($envs.Count -gt 0) {
        Add-Result -Check "Environment visibility" -Status "pass" -Details "Visible environments: $($envs.Count)"
      } else {
        Add-Result -Check "Environment visibility" -Status "fail" -Details "No environments visible" -RequestIfMissing "Request access to at least one Power Platform environment"
      }
    } catch {
      Add-Result -Check "Environment visibility" -Status "fail" -Details $_.Exception.Message -RequestIfMissing "Request Power Platform environment access"
    }

    if ($EnvironmentName -and $envs.Count -gt 0) {
      $selectedEnv = $envs | Where-Object { $_.EnvironmentName -eq $EnvironmentName -or $_.DisplayName -eq $EnvironmentName } | Select-Object -First 1
      if ($selectedEnv) {
        Add-Result -Check "Target environment found" -Status "pass" -Details "Found environment: $($selectedEnv.DisplayName) ($($selectedEnv.EnvironmentName))"
      } else {
        Add-Result -Check "Target environment found" -Status "fail" -Details "Environment '$EnvironmentName' not found" -RequestIfMissing "Request access to environment '$EnvironmentName'"
      }
    } elseif ($envs.Count -gt 0) {
      Add-Result -Check "Target environment parameter" -Status "info" -Details "No -EnvironmentName supplied; run again with a specific target env for deeper checks."
    }

    # 6) Connector API permissions (best effort)
    try {
      $connectors = @(Get-AdminPowerAppConnector)
      Add-Result -Check "Connector metadata access" -Status "pass" -Details "Can list connector metadata (count: $($connectors.Count))"
    } catch {
      Add-Result -Check "Connector metadata access" -Status "warn" -Details $_.Exception.Message -RequestIfMissing "Request permission to create/manage custom connectors in target environment"
    }

    # 7) Copilot Studio capabilities (best effort)
    Add-Result -Check "Copilot Studio maker rights" -Status "info" -Details "Automatic role introspection is limited via current modules. Validate manually in environment security roles/UI." -RequestIfMissing "Request Copilot Studio maker access + ability to create/edit copilots and actions"

    # 8) DLP awareness
    Add-Result -Check "DLP policy compatibility" -Status "info" -Details "Cannot fully validate DLP via this script. Admin must confirm custom connector allowed in this environment." -RequestIfMissing "Request DLP exception/approval for AIKB custom connector usage"
  }
}

# Summarize missing asks
$missing = $Results | Where-Object { $_.status -in @('fail','warn') -and $_.request_if_missing }
$asks = $missing | Select-Object -ExpandProperty request_if_missing -Unique

$report = [PSCustomObject]@{
  generated_utc = (Get-Date).ToUniversalTime().ToString("s") + "Z"
  machine = $env:COMPUTERNAME
  user = $env:USERNAME
  environment_name = $EnvironmentName
  results = $Results
  required_requests = $asks
}

$report | ConvertTo-Json -Depth 8 | Set-Content -Path $OutputPath -Encoding UTF8

Write-Host ""
Write-Host "== Summary ==" -ForegroundColor Cyan
$Results | Format-Table -AutoSize
Write-Host ""
Write-Host "Report written to: $OutputPath" -ForegroundColor Green

if ($asks.Count -gt 0) {
  Write-Host ""
  Write-Host "== Access Requests to Send Admin ==" -ForegroundColor Yellow
  $i = 1
  foreach ($a in $asks) {
    Write-Host "$i. $a"
    $i++
  }

  Write-Host ""
  Write-Host "== Email/Ticket Template ==" -ForegroundColor Yellow
  $template = @"
Hello IT/Power Platform Admin,

I am onboarding an AIKB integration with Microsoft Copilot Studio in environment '$EnvironmentName'.
Please grant/confirm the following access:

$($asks | ForEach-Object { "- $_" } | Out-String)

Purpose:
- Import and configure a custom connector from OpenAPI
- Create connector connections
- Add connector actions to a Copilot Studio copilot (remember/recall/context-pack)

Thank you.
"@
  Write-Host $template
}

# Exit non-zero if hard failures exist
$hardFail = $Results | Where-Object { $_.status -eq 'fail' }
if ($hardFail.Count -gt 0) {
  exit 2
}

exit 0

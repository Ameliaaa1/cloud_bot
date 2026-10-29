param(
  [string]$Message = "chore: weekly project update"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
  $changes = git status --short
  if (-not $changes) { Write-Host "No changes to publish."; exit 0 }
  git add --all
  git commit -m $Message
  git push origin main
} finally { Pop-Location }


param(
  [string]$Port = "COM5"
)

$ErrorActionPreference = "Stop"
$cli = Join-Path $env:USERPROFILE "ArduinoCLI\arduino-cli.exe"
$sketch = Join-Path $PSScriptRoot "..\firmware\cloud_bot_existing_parts"
$fqbn = "esp32:esp32:esp32cam"

if (-not (Test-Path -LiteralPath $cli)) {
  throw "Arduino CLI not found at $cli"
}

& $cli compile --fqbn $fqbn $sketch
if ($LASTEXITCODE -ne 0) { throw "Compile failed" }
& $cli upload -p $Port --fqbn $fqbn $sketch
if ($LASTEXITCODE -ne 0) { throw "Upload failed on $Port" }
Write-Host "cloud_bot uploaded successfully to $Port"


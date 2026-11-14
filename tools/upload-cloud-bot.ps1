param(
  [string]$Port = ""
)

$ErrorActionPreference = "Stop"
$cli = Join-Path $env:USERPROFILE "ArduinoCLI\arduino-cli.exe"
$sketch = Join-Path $PSScriptRoot "..\firmware\cloud_bot_existing_parts"
$fqbn = "esp32:esp32:esp32cam"

if (-not (Test-Path -LiteralPath $cli)) {
  throw "Arduino CLI not found at $cli"
}

if (-not $Port) {
  $devices = (& $cli board list --format json | ConvertFrom-Json).detected_ports
  $candidates = @($devices | Where-Object { $_.port.properties.vid -eq "0x1A86" -and $_.port.properties.pid -eq "0x7523" })
  if ($candidates.Count -ne 1) { throw "Specify -Port explicitly; expected exactly one CH340 USB device." }
  $Port = $candidates[0].port.address
}



& $cli compile --fqbn $fqbn $sketch
if ($LASTEXITCODE -ne 0) { throw "Compile failed" }
& $cli upload -p $Port --fqbn $fqbn $sketch
if ($LASTEXITCODE -ne 0) { throw "Upload failed on $Port" }
Write-Host "cloud_bot uploaded successfully to $Port"

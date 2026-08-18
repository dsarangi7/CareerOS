$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { $Python = "python" }
& $Python -m scripts.tasks scan-tier-a
if ($LASTEXITCODE -ne 0) { throw "CareerOS Tier A scan failed." }

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { $Python = "python" }
& $Python -m scripts.tasks scan-tier-c
if ($LASTEXITCODE -ne 0) { throw "CareerOS Tier C scan failed." }

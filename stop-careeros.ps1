$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $Root "private_data\runtime"
$PidFile = Join-Path $RuntimeDir "careeros-processes.json"

if (-not (Test-Path -LiteralPath $PidFile)) {
    Write-Host "No CareerOS launcher PID file found. Nothing to stop."
    exit 0
}

$state = Get-Content -LiteralPath $PidFile -Raw | ConvertFrom-Json
$pids = @($state.api_pid, $state.dashboard_pid) | Where-Object { $_ }
$stopped = @()

foreach ($pid in $pids) {
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        continue
    }
    try {
        Stop-Process -Id $pid -Force
        $stopped += $pid
    } catch {
        Write-Host "Could not stop CareerOS process ${pid}: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Remove-Item -LiteralPath $PidFile -Force

if ($stopped.Count -eq 0) {
    Write-Host "No running CareerOS launcher processes were found."
} else {
    Write-Host "Stopped CareerOS launcher process PID(s): $($stopped -join ', ')" -ForegroundColor Green
}

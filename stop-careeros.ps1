$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $Root "private_data\runtime"
$PidFile = Join-Path $RuntimeDir "careeros-processes.json"

if (-not (Test-Path -LiteralPath $PidFile)) {
    Write-Host "No CareerOS launcher PID file found. Nothing to stop."
    exit 0
}

$state = Get-Content -LiteralPath $PidFile -Raw | ConvertFrom-Json
$targets = @(
    [PSCustomObject]@{ Name = "FastAPI backend"; Pid = $state.api_pid; StartedAt = $state.api_start_time },
    [PSCustomObject]@{ Name = "Streamlit dashboard"; Pid = $state.dashboard_pid; StartedAt = $state.dashboard_start_time }
)
$stopped = @()

foreach ($target in $targets) {
    $pid = $target.Pid
    if (-not $pid) {
        continue
    }
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        continue
    }
    try {
        if ($target.StartedAt) {
            $recordedStart = [DateTime]::Parse($target.StartedAt)
            $delta = [Math]::Abs(($process.StartTime.ToUniversalTime() - $recordedStart.ToUniversalTime()).TotalSeconds)
            if ($delta -gt 2) {
                Write-Host "Skipping PID ${pid}; it no longer matches the launcher-started $($target.Name) process." -ForegroundColor Yellow
                continue
            }
        }
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

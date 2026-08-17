$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$RuntimeDir = Join-Path $Root "private_data\runtime"
$PidFile = Join-Path $RuntimeDir "careeros-processes.json"
$ApiUrl = "http://127.0.0.1:8000/health"
$DashboardUrl = "http://localhost:8501"
$ApiLog = Join-Path $RuntimeDir "api.log"
$ApiErr = Join-Path $RuntimeDir "api.err.log"
$DashboardLog = Join-Path $RuntimeDir "dashboard.log"
$DashboardErr = Join-Path $RuntimeDir "dashboard.err.log"

function Fail($Message) {
    Write-Host "CareerOS launcher error: $Message" -ForegroundColor Red
    exit 1
}

function Test-HttpReady($Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500)
    } catch {
        return $false
    }
}

function Wait-ForService($Name, $Url, $Process) {
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        if ($Process.HasExited) {
            Fail "$Name exited before becoming healthy. Check logs in $RuntimeDir."
        }
        if (Test-HttpReady $Url) {
            Write-Host "$Name is healthy at $Url" -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 1
        $Process.Refresh()
    }
    Fail "$Name did not become healthy at $Url within 60 seconds. Check logs in $RuntimeDir."
}

function Stop-StartedProcesses($Processes) {
    foreach ($process in $Processes) {
        try {
            if ($process -and -not $process.HasExited) {
                Stop-Process -Id $process.Id -Force
            }
        } catch {
            Write-Host "Could not stop process $($process.Id): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

Set-Location $Root
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Fail "Virtual environment not found at .venv. Run: python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install ."
}

if (Test-Path -LiteralPath $PidFile) {
    $existing = Get-Content -LiteralPath $PidFile -Raw | ConvertFrom-Json
    $running = @()
    foreach ($pid in @($existing.api_pid, $existing.dashboard_pid)) {
        if ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
            $running += $pid
        }
    }
    if ($running.Count -gt 0) {
        Fail "CareerOS already appears to be running with PID(s): $($running -join ', '). Use .\stop-careeros.ps1 first."
    }
}

Write-Host "Verifying installed dependencies..."
& $VenvPython -c "import fastapi, sqlalchemy, pydantic, uvicorn, streamlit, pandas, openpyxl, plotly, pypdf, reportlab"
if ($LASTEXITCODE -ne 0) {
    Fail "Dependency check failed. Activate .venv and run: python -m pip install ."
}

Write-Host "Running database migrations..."
& $VenvPython -m scripts.tasks migrate
if ($LASTEXITCODE -ne 0) {
    Fail "Database migration command failed."
}

$started = @()
try {
    Write-Host "Starting FastAPI backend on localhost..."
    $api = Start-Process `
        -FilePath $VenvPython `
        -ArgumentList @("-m", "uvicorn", "app.api.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $ApiLog `
        -RedirectStandardError $ApiErr `
        -WindowStyle Hidden `
        -PassThru
    $started += $api

    Write-Host "Starting Streamlit dashboard on localhost..."
    $dashboard = Start-Process `
        -FilePath $VenvPython `
        -ArgumentList @("-m", "streamlit", "run", "dashboard/Home.py", "--server.address", "127.0.0.1", "--server.port", "8501", "--browser.gatherUsageStats", "false", "--server.headless", "true") `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $DashboardLog `
        -RedirectStandardError $DashboardErr `
        -WindowStyle Hidden `
        -PassThru
    $started += $dashboard

    $state = [PSCustomObject]@{
        api_pid = $api.Id
        dashboard_pid = $dashboard.Id
        api_url = $ApiUrl
        dashboard_url = $DashboardUrl
        started_at = (Get-Date).ToString("o")
        root = $Root
    }
    $state | ConvertTo-Json | Set-Content -LiteralPath $PidFile -Encoding UTF8

    Wait-ForService "FastAPI backend" $ApiUrl $api
    Wait-ForService "Streamlit dashboard" $DashboardUrl $dashboard

    Write-Host "Opening CareerOS dashboard at $DashboardUrl"
    Start-Process $DashboardUrl
    Write-Host "CareerOS is running. Use .\stop-careeros.ps1 to stop only these launcher-started processes." -ForegroundColor Green
} catch {
    Stop-StartedProcesses $started
    if (Test-Path -LiteralPath $PidFile) {
        Remove-Item -LiteralPath $PidFile -Force
    }
    Fail $_.Exception.Message
}

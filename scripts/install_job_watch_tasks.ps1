param(
    [ValidateSet("A", "B", "C")]
    [string]$Tier = "A",
    [string]$TaskName = "CareerOS-JobWatch-TierA",
    [string]$Time = "07:00"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "CareerOS virtual environment not found at $Python. Run setup before installing tasks."
}

$scriptByTier = @{
    A = "run_tier_a_scan.ps1"
    B = "run_tier_b_scan.ps1"
    C = "run_tier_c_scan.ps1"
}
$TaskMap = @(
    @{ Name = "CareerOS-JobWatch-TierA"; Script = "run_tier_a_scan.ps1"; Days = @("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN") },
    @{ Name = "CareerOS-JobWatch-TierB"; Script = "run_tier_b_scan.ps1"; Days = @("MON", "WED", "FRI") },
    @{ Name = "CareerOS-JobWatch-TierC"; Script = "run_tier_c_scan.ps1"; Days = @("MON") },
    @{ Name = "CareerOS-JobWatch-WeeklyReport"; Script = "run_weekly_report.ps1"; Days = @("MON") }
)

foreach ($task in $TaskMap) {
    $taskScript = Join-Path $PSScriptRoot $task.Script
    if (-not (Test-Path -LiteralPath $taskScript)) {
        throw "Missing task script: $taskScript"
    }
    $action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$taskScript`"" -WorkingDirectory $Root
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $task.Days -At $Time
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    Register-ScheduledTask -TaskName $task.Name -Action $action -Trigger $trigger -Settings $settings -Description "CareerOS job watchlist scan task" -Force | Out-Null
    Write-Host "Installed $($task.Name) at $Time Asia/Shanghai local time."
}

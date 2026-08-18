$ErrorActionPreference = "Stop"
$TaskNames = @(
    "CareerOS-JobWatch-TierA",
    "CareerOS-JobWatch-TierB",
    "CareerOS-JobWatch-TierC",
    "CareerOS-JobWatch-WeeklyReport"
)
foreach ($name in $TaskNames) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
        Write-Host "Removed $name"
    }
}

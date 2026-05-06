param(
    [string]$ArchiveRoot = "local_artifacts/logs"
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$archivePath = Join-Path $projectRoot $ArchiveRoot
New-Item -ItemType Directory -Force -Path $archivePath | Out-Null

$patterns = @("*.log", "*.out.log", "*.err.log")
$moved = @()

foreach ($pattern in $patterns) {
    Get-ChildItem -Path $projectRoot -Filter $pattern -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notlike "$archivePath*" } |
        ForEach-Object {
            $destination = Join-Path $archivePath $_.Name
            Move-Item -LiteralPath $_.FullName -Destination $destination -Force
            $moved += $destination
        }
}

Write-Host "Moved $($moved.Count) local log files to $archivePath"
if ($moved.Count -gt 0) {
    $moved | ForEach-Object { Write-Host " - $_" }
}

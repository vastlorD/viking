param(
    [Parameter(Mandatory = $true)][string]$Target,
    [string]$Baseline = "baseline.json",
    [string]$KeyFile = ".integrity-key",
    [string]$Report = "reports/latest.json"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
try {
    & py -3.12 -m integrity_guard check $Target --baseline $Baseline --key-file $KeyFile --report $Report
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}

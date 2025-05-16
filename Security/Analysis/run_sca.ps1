$OutputDir = "Security/Analysis/SCA"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# pip-audit
$i = 1
do {
    $pipFile = "$OutputDir/relatorio_pip_auditv$i.txt"
    $i++
} while (Test-Path $pipFile)

Write-Output "Running pip-audit → $pipFile"
pip-audit > $pipFile

# Snyk
$i = 1
do {
    $snykFile = "$OutputDir/relatorio_snykv$i.json"
    $i++
} while (Test-Path $snykFile)

# Detetar o requirements.txt
$reqPath = Get-ChildItem -Path . -Recurse -Filter requirements.txt | Select-Object -First 1
if ($reqPath) {
    Write-Output "Running Snyk on $($reqPath.FullName) → $snykFile"
    snyk test --file="$($reqPath.FullName)" --json > $snykFile
} else {
    Write-Warning "❌ requirements.txt not found. Skipping Snyk."
}

Write-Output "✅ SCA completed: $pipFile + $snykFile"

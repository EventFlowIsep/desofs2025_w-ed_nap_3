$OutputDir = "Security/Analysis/SAST"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# BANDIT
$i = 1
do {
    $banditFile = "$OutputDir/relatorio_banditv$i.html"
    $i++
} while (Test-Path $banditFile)

Write-Output "Running Bandit → $banditFile"
bandit -r . -f html -o $banditFile

# SEMGREP (via Docker)
$i = 1
do {
    $semgrepFile = "$OutputDir/relatorio_semgrepv$i.txt"
    $i++
} while (Test-Path $semgrepFile)

Write-Output "Running Semgrep (Docker) → $semgrepFile"
docker run --rm -v "${PWD}:/src" returntocorp/semgrep semgrep --config auto --output "/src/$semgrepFile"

Write-Output "✅ SAST completed: $banditFile + $semgrepFile"

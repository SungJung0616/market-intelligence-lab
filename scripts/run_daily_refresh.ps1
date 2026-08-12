$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
& uv run --env-file .env python -m market_intelligence_lab.jobs.run_daily_refresh
exit $LASTEXITCODE

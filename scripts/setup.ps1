# Create the ONE virtual environment this repo uses, install the precompute lane and the editable
# package. Idempotent, re-runnable, no global installs. PowerShell parity of setup.sh; see that file
# for why the previous two-venv split (`.venv-pipeline` plus `.venv`) was removed rather than fixed.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$py = if ($env:PYTHON) { $env:PYTHON } else { "python" }

if (-not (Test-Path ".venv")) { & $py -m venv .venv }
$vp = Join-Path ".venv" "Scripts\python.exe"
if (-not (Test-Path $vp)) { $vp = Join-Path ".venv" "bin/python" }

Write-Host "[setup] .venv, precompute lane..."
& $vp -m pip install --upgrade pip -q
& $vp -m pip install -q -r requirements-precompute.txt -r requirements-dev.txt
& $vp -m pip install -q -e .
Write-Host "[setup] .venv ready."

Write-Host ""
Write-Host "[setup] done. Next:"
Write-Host "  ./scripts/precompute.ps1 all --expand   bake every case"
Write-Host "  ./scripts/dev.ps1                       serve the app"

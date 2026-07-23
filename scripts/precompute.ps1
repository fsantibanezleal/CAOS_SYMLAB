# Run the offline pipeline (pass-through args). Examples:
#
#   ./scripts/precompute.ps1 monod-saturation           one generator case
#   ./scripts/precompute.ps1 flotation-silica --seed 7   one real-data case at another seed
#   ./scripts/precompute.ps1 all --expand                every case, benchmark suites expanded
#   ./scripts/precompute.ps1 --list                      what the registry declares
#
# `all` WITHOUT `--expand` fails on the two benchmark suites, which are expanded into one case per
# problem rather than run as a single case.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$vp = Join-Path ".venv" "Scripts\python.exe"
if (-not (Test-Path $vp)) { $vp = Join-Path ".venv" "bin/python" }
if (-not (Test-Path $vp)) {
  Write-Error "no interpreter under .venv. Create it first: python -m venv .venv; .venv\Scripts\pip install -e data-pipeline"
}
& $vp -m symlab.pipeline @args

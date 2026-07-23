#!/usr/bin/env bash
# Run the offline pipeline (pass-through args). Examples:
#
#   ./scripts/precompute.sh monod-saturation           one generator case
#   ./scripts/precompute.sh flotation-silica --seed 7   one real-data case at another seed
#   ./scripts/precompute.sh all --expand                every case, benchmark suites expanded
#   ./scripts/precompute.sh --list                      what the registry declares
#
# `all` WITHOUT `--expand` fails on the two benchmark suites, which are expanded into one case per
# problem rather than run as a single case.
set -euo pipefail
cd "$(dirname "$0")/.."
VP=".venv/bin/python"; [ -x "$VP" ] || VP=".venv/Scripts/python.exe"
if [ ! -x "$VP" ]; then
  echo "no interpreter under .venv. Create it first:" >&2
  echo "  python -m venv .venv && .venv/Scripts/pip install -e data-pipeline" >&2
  exit 1
fi
"$VP" -m symlab.pipeline "$@"

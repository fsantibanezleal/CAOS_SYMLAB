#!/usr/bin/env bash
# Create the ONE virtual environment this repo uses, install the precompute lane and the editable
# package. Idempotent, re-runnable, no global installs.
#
# There used to be two venvs here, `.venv-pipeline` for a "heavy OFFLINE lane" and `.venv` for a
# "runtime/live-thin lane". Neither half held up, and only `.venv` was ever created, so every guide
# that told a reader to run `.venv-pipeline/bin/python` was giving an instruction that could not work.
#
# There is no heavy lane: the engine is hand-written numpy precisely so the same modules can run in
# the browser, and the only dependencies beyond numpy are two spreadsheet readers and the evaluation
# harness. And there is no thin runtime lane to install, because the live lane runs in the READER'S
# BROWSER through Pyodide, which resolves its own wheels and has never read a venv.
#
# So `requirements.txt` is not an install target here. It declares what the browser lane is allowed
# to import, which is why it is kept to numpy alone. The separation that matters is between those two
# FILES, not between two directories on this machine.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python}"

[ -d .venv ] || "$PY" -m venv .venv
VP=".venv/bin/python"; [ -x "$VP" ] || VP=".venv/Scripts/python.exe"

echo "[setup] .venv, precompute lane..."
"$VP" -m pip install --upgrade pip -q
"$VP" -m pip install -q -r requirements-precompute.txt -r requirements-dev.txt
"$VP" -m pip install -q -e .
echo "[setup] .venv ready."

echo
echo "[setup] done. Next:"
echo "  ./scripts/precompute.sh all --expand   bake every case"
echo "  ./scripts/dev.sh                       serve the app"

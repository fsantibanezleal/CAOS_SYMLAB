# scripts/

Everything here is runnable locally, and everything in the guards table runs in CI too. Anything with
a shell counterpart ships in BOTH `*.sh` (macOS, Linux, Git Bash) and `*.ps1` (Windows PowerShell),
because this repository is developed on Windows and deployed from Linux runners.

They are idempotent, they detect `.venv/bin/python` against `.venv/Scripts/python.exe`, and they pin
nothing: versions live in `requirements-*.txt`.

## Environment and running

| Script | What it does |
|---|---|
| `setup.{sh,ps1}` | Creates `.venv`, upgrades pip, installs `requirements-precompute.txt` plus `requirements-dev.txt` plus the editable package. There is ONE venv; see the comment at the top of `setup.sh` for why the previous two-venv split was removed. |
| `precompute.{sh,ps1}` | Runs the staged pipeline, passing arguments straight through: `precompute.sh all --expand` for everything, `precompute.sh monod-saturation --seed 7` for one case. `all` WITHOUT `--expand` fails on the two benchmark suites. |
| `dev.{sh,ps1}` | Starts the frontend dev server, and uvicorn too if the dormant API lane has been activated. |
| `smoke.{sh,ps1}` | The CONTRACT 2 check end to end: index against manifests against artifacts. |
| `fetch_data.py` | Stages raw sources into the vault outside the repository. Raw data is never committed. |

## Guards

| Script | What it enforces |
|---|---|
| `check_artifacts.py` | Every manifest has its artifact and vice versa, every declared byte count matches disk, no artifact is empty, the recorded lane matches the gate verdict, and nothing on disk is missing from the index. That last check exists because walking the index alone once reported "OK: 1 cases" with 24 artifacts on disk. |
| `check_template_residue.py` | An instantiated product must not ship template residue: the example lab, the SIR model, `EX0*` cases, placeholder text. No-op in the template itself while the `.template-source` sentinel exists. It scans `.csv` and `.tsv` as well as source and prose, because the residue it missed for months was a `.csv`. See ADR-0057 and ADR-0061. |
| `check_content_standards.py` | No em-dash (`U+2014`, `U+2015`) and no pictographic emoji in tracked content. Use a comma, colon, semicolon, period, parentheses or a middot instead. See ADR-0067. |

## Generators, run after a bake

These exist because a number written by hand is a number that will be wrong. Each has a test behind
it that fails when its output drifts from the code.

| Script | What it regenerates |
|---|---|
| `rebuild_index.py` | `manifests/index.json` from the artifacts on disk. |
| `sync_case_doc_truth_rows.py` | The truth and regime rows in `docs/cases/*.md`, and the counts block in `docs/cases.md`, from the registry. |
| `sync_readme_headline.py` | The headline measurement table in `README.md`, from a committed artifact. |
| `measure_rung_costs.py` | The cost of each ladder rung against the Koza baseline, quoted in four places. Prints; reconcile by hand. |

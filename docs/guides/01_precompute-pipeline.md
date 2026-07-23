# Guide, run the precompute pipeline

```bash
./scripts/setup.sh                      # or scripts/setup.ps1, builds .venv, installs, editable pkg
./scripts/precompute.sh all --expand    # every case (or: ./scripts/precompute.sh monod-saturation --seed 7)
.venv/bin/python -m pytest              # Scripts/python.exe on Windows
./scripts/smoke.sh                      # CONTRACT 2 check: index <-> manifests <-> artifacts consistent
```

There is ONE venv, `.venv`, holding `requirements-precompute.txt` plus `requirements-dev.txt` plus the
editable package. This guide used to describe two, `.venv-pipeline` for a heavy offline lane and `.venv`
for a thin runtime lane, and told you to run `.venv-pipeline/bin/python`. That interpreter was never
created by anyone: there is no heavy lane, because the engine is hand-written numpy so the same modules
can run in the browser, and there is no thin runtime lane to install, because the live lane runs in the
reader's browser through Pyodide, which resolves its own wheels and never reads a venv.

So `requirements.txt` is not something you install. It declares what the browser lane is allowed to
import, which is why it is numpy alone, and the separation that matters is between it and
`requirements-precompute.txt` rather than between two directories.

`precompute.{sh,ps1}` passes its arguments straight through to `python -m symlab.pipeline`, so `--seed`,
`--noise`, `--quick`, `--expand` and `--list` all work from there. `--expand` turns the two suite cases
into one case per underlying problem, and `all` WITHOUT it fails on those two suites rather than skipping
them.

Outputs land in `data/derived/<case>/run.json`, `manifests/<case>.json` and `manifests/index.json`. The
manifests sit at the repository root, next to the pipeline that writes them, not inside the derived tree.

Set `SYMLAB_OUTPUT_DIR` to redirect the whole output tree somewhere disposable. Do that whenever you are
experimenting or running a test that bakes, because without it a `--quick` run overwrites a published
full-budget artifact in place, which has cost this line a release before.

The run is deterministic in `(case, config, seed, data)`: the same seed reproduces every scientific number
exactly, and only the measured wall clock varies. Stages and their roles:
[../architecture/05_precompute-pipeline.md](../architecture/05_precompute-pipeline.md).

# The staged precompute pipeline

`data-pipeline/symlab/pipeline.py` orchestrates the **named stages** (frozen names/signatures, rework bodies):

| Stage | Module | Does |
|---|---|---|
| preprocess | `stages/preprocess.py` | load the raw source, apply **CONTRACT 1** (`_contract_check`), split, and resolve the scoring truth and its regime |
| feature_extraction | `stages/feature_extraction.py` | validated dataset to feature rows, sampling ranges and the units-declared flag |
| train | `stages/train.py` | run the search, dispatching on the FAMILY: the GP ladder, where each rung adds ONE mechanism, and the non-evolutionary sparse arm |
| infer | `stages/infer.py` | render each front member: LaTeX with node ids, tree, terms, influence |
| evaluate | `stages/evaluate.py` | held-out, leakage-safe metrics (R2 and mean squared error) plus the equivalence verdict |
| export | `stages/export.py` | **CONTRACT 2**, compact artifact + manifest |

`run_case` also builds the bounded-exhaustive **certificate**, but only on a full run with three inputs or
fewer; `--quick` and wider cases skip it and the app says so rather than showing an empty panel.

Run: `python -m symlab.pipeline [all|<case_id>] [--seed N] [--noise F] [--quick] [--expand] [--list]` (or
`scripts/precompute.{sh,ps1}`). `--expand` turns the two suite cases (`feynman-suite`, `strogatz-dynamics`)
into one case per underlying problem, taking the 25 registry cases to 55 runnable ones (18 Feynman problems and
14 Strogatz systems replace their two parents); 39 of those are baked and committed today. `--quick` is a
reduced budget for a smoke run and must never produce published numbers. `SYMLAB_OUTPUT_DIR` redirects the
whole output tree, which is how a test bakes without overwriting the published artifacts.

It writes `data/derived/<case>/run.json`, `manifests/<case>.json` and `manifests/index.json`. The manifests sit
at the repository root next to the pipeline that writes them, not inside the derived tree; the derived tree
holds only the artifacts the web serves, and `frontend/copy-data.mjs` copies both into `frontend/public/data/`.

The search engine is in-repo (`symlab/search/`, pure Python plus numpy) rather than a third-party framework.
The one external research dependency in the scoring path is `sreval[symbolic]==0.1.0` (MIT), pinned in
`requirements-precompute.txt` and used by `stages/evaluate.py` for the structural distance; the frameworks the
research examined and the reasons for not adopting them are in [../frameworks/](../frameworks/). Note that
`data-pipeline/requirements.txt` is a one-line pointer at `requirements-precompute.txt`, kept so two files
cannot claim the same lane and drift apart.

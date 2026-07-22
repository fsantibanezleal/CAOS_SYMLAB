# The staged precompute pipeline

`data-pipeline/symlab/pipeline.py` orchestrates the **named stages** (frozen names/signatures, rework bodies):

| Stage | Module | Does |
|---|---|---|
| preprocess | `stages/preprocess.py` | read raw to apply **CONTRACT 1** (validate + outlier policy) |
| feature_extraction | `stages/feature_extraction.py` | validated params to feature rows |
| train | `stages/train.py` | run the search, dispatching on the FAMILY: the GP ladder, where each rung adds ONE mechanism, and the non-evolutionary sparse arm |
| infer | `stages/infer.py` | render each front member: LaTeX with node ids, tree, terms, influence |
| evaluate | `stages/evaluate.py` | held-out, leakage-safe metrics (R²/RMSE) |
| export | `stages/export.py` | **CONTRACT 2**, compact artifact + manifest |

Run: `python -m symlab.pipeline [all|<case_id>] [--seed N]` (or `scripts/precompute.{sh,ps1}`). It writes
`data/derived/<case>/trace.json` + `data/derived/manifests/<case>.json` + `index.json`.

To instantiate a real product: keep the stage names, replace the bodies, `infer`/`train` call the
research-chosen SOTA engine (pinned in `data-pipeline/requirements.txt`, documented in
[../frameworks/](../frameworks/)). No hand-rolled toy substitute for an engine the research prescribed.

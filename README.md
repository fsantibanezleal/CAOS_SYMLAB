# SymLab

[![CI](https://img.shields.io/github/actions/workflow/status/fsantibanezleal/CAOS_SYMLAB/ci.yml?branch=main&label=CI)](https://github.com/fsantibanezleal/CAOS_SYMLAB/actions)
[![License](https://img.shields.io/github/license/fsantibanezleal/CAOS_SYMLAB)](LICENSE)
[![Version](https://img.shields.io/github/v/tag/fsantibanezleal/CAOS_SYMLAB?label=version&sort=semver)](https://github.com/fsantibanezleal/CAOS_SYMLAB/tags)
[![Live](https://img.shields.io/badge/live-symlab.fasl--work.com-2ea44f)](https://symlab.fasl-work.com)

A public research lab on **symbolic regression**: recovering an explicit closed-form expression from
data, rather than fitting a predictor nobody can read.

Live at **[symlab.fasl-work.com](https://symlab.fasl-work.com)**.

## The measurement this exists to make

Accuracy and recovery are different claims, and a method can clear R2 > 0.999 while returning a
structure that has nothing in common with the law that generated the data. On a scientific-discovery
benchmark a pretrained transformer reached 26.7 percent of problems above R2 0.999 with a 0.00
percent solution rate and a normalised edit distance of 1.00: a near-perfect fit, the wrong
structure, every time.

So this lab reports the two **separately, on every case, and never averages them into one number**.

Measured here on the Feynman Gaussian, with both search families at published budgets:

| Family | Configuration | R2 (test) | Recovered | Seconds |
|---|---|---|---|---|
| genetic programming | Koza baseline | 0.989307 | no | 3.97 |
| genetic programming | + linear scaling | 1 - 6.0e-6 | no | 3.03 |
| genetic programming | + deduplication | 0.996795 | no | 153.25 |
| sparse regression | non-evolutionary arm | 1 - 1.8e-9 | no | 0.01 |

Two method families with nothing in common, one reaching a near-perfect fit in ten milliseconds, and
neither recovers the law. Every accuracy-only benchmark scores this as solved.

Where a case has **no published closed form**, recovery is reported as "not checkable" rather than as
zero. Reporting an unmeasurable quantity as a failure would be a false statement about the method.

## What is in here

- **Two search families.** A genetic-programming ladder where each rung adds exactly ONE mechanism to
  the one above it, so a measured difference is attributable to a named change; and a
  non-evolutionary arm (a fixed nonlinear library with sequentially thresholded least squares, the
  FFX and SINDy family) which is deterministic, produces its front by construction, and runs in
  milliseconds. A ladder of GP rungs alone is an ablation of GP, not a survey of the field.
- **25 cases** across physics with published laws, industrial process, mining and metallurgy, biology
  and ecology, environment and energy, and first-principles generators. Seven are real measured data.
- **35 verified truth expressions**: 17 of 18 generators, 17 of 18 selected Feynman laws, and one
  exact identity over real plant data. Each is checked against its own data before it is allowed to
  score, because a wrong truth publishes a confident "not recovered" against a method that succeeded.
- **A live lane.** The same Python engine runs in the browser through Pyodide at a reduced budget, so
  the published numbers are checkable rather than merely asserted.
- **A `docs/` wiki**: the architecture, seven method families with their mathematics and citations,
  22 framework cards with licences and whether this repo uses each one, and a page per case.

## The two data contracts

1. **Ingestion, raw to pipeline.** Enforced in `stages/preprocess.py`. A dataset is refused, not
   coerced, when it carries non-finite values, a constant input column, or a target whose
   distinct-value count means fitting at that resolution would leak it. Everything the loader had to
   do (rows dropped, folds ignored, aggregation applied) is recorded and published.
2. **Artifact, pipeline to web.** Frozen at `schema_version 1.0.0` in `core/contract.py`, mirrored in
   TypeScript, and asserted from BOTH sides: a field the producer stops writing, or writes without
   declaring, compiles perfectly and would otherwise ship silently.

## Quickstart

```bash
./scripts/setup.sh                      # or scripts/setup.ps1 on Windows
./scripts/precompute.sh                 # the offline pipeline, into data/derived/ and manifests/
.venv/bin/python -m pytest              # .venv/Scripts/python.exe on Windows
cd frontend && npm install && node copy-data.mjs && npm run dev
```

To run it on your own data, see [docs/guides/02_bring-your-own-data.md](docs/guides/02_bring-your-own-data.md).
To read the app, see [docs/guides/00_read-the-workbench.md](docs/guides/00_read-the-workbench.md).

## Honesty commitments, and the guards behind them

Each of these exists because the corresponding defect survived a green build:

- Every number on the site is replayed from a committed artifact produced by a seeded offline run.
- Booleans are exported as booleans. They were integers, because `bool` subclasses `int` in Python,
  and the dimensional-consistency warning could therefore never render.
- Floats round to SIGNIFICANT digits, not decimal places. Decimal rounding published a mean squared
  error of 6.1e-12 as "0.0" and an R-squared of 0.999999998 as "1.0", which are claims of an exact
  fit, printed beside a verdict saying the law was not found.
- No artifact may report zero loss beside a failed recovery. A zero loss is legitimate when the law
  WAS recovered; the contradiction is not.
- A published expression must reproduce the loss reported for it. The non-evolutionary arm once
  fitted one function and published another.
- Source defects are recorded verbatim rather than tidied away. Four sources the research had marked
  good turned out to be defective on download, and every one returned HTTP 200.

## Licence

MIT. Data sources carry their own licences, stated per case in `docs/cases/` and in each artifact.
The evaluation harness is published separately as [`sreval`](https://pypi.org/project/sreval/) (MIT).

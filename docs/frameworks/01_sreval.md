# Framework card, sreval

**Status in this repo: USED.** It is the only symbolic-regression package this repo depends on, and
the evaluation stage CALLS it: `structural_distance` in `stages/evaluate.py` delegates to
`sreval.equivalence.structural_distance` whenever the package is installed. The usage snippet below
was checked against the installed 0.1.0 API on 2026-07-22.

## What it is, and the one thing it does better

`sreval` is an evaluation harness for symbolic regression: given a candidate expression and a known
truth, it decides whether the candidate is the same expression, and it reports accuracy and recovery
as two separate numbers that it refuses to merge.

The one thing it does better than the alternatives is that it publishes the failure rate of its own
symbolic test as a first-class output. Every published SR benchmark runs a sympy simplification to
decide equivalence, and that simplification times out or throws on a non-trivial fraction of real
cases. SRBench's own postprocessing scores those cases as method failures (see
[03_srbench.md](03_srbench.md)), which charges the search for a defect in the scorer. `sreval` runs
three independent tests instead of one, reports them separately, reports whether they agreed, and
reports how often the symbolic test could not decide.

| Test | What it is good for | How it fails |
|---|---|---|
| Symbolic (sympy) | Exact when it terminates | Times out, throws, or fails to reduce a genuinely zero difference |
| Numerical probing | Cheap and robust to the simplifier's limits | Cannot separate "equivalent everywhere" from "agrees on the sampled box", which is exactly what breaks under extrapolation |
| Structural edit distance | The only graded verdict, so "wrong by one term" is distinguishable from "wrong entirely" | Sensitive to algebraically equivalent rewrites a reader would call the same answer |

## What this card claimed before, and what was true

This card said the package was used in `stages/evaluate.py`. It was imported there, pinned in
`requirements-precompute.txt`, and never called: nothing in the module referenced the imported
names. The dependency was decoration, and the card asserted otherwise.

`structural_distance` now delegates to `sreval.equivalence.structural_distance` when the package is
installed, keeping the local implementation as the fallback for the browser lane, which never
installs it. `tests/test_sreval_agrees.py` asserts the two produce identical numbers across every
generator truth and across the shapes where an edit-distance metric usually goes wrong, because a
browser run and an offline run reporting different structural distances would contradict the app's
own claim that they are the same engine.


## Licence, and whether this MIT repo may use it

MIT (`LICENSE`, copyright 2026 Felipe Santibanez-Leal), declared as `license = { text = "MIT" }` in
its `pyproject.toml`. Same licence as this repo, so it may be depended on, vendored or forked without
restriction.

## Install reality

Pure Python. `dependencies = ["numpy>=1.24"]`, `requires-python = ">=3.10"`, with a `symbolic` extra
that adds `sympy>=1.12`. No compiler, no Julia, no GPU.

Source repository: `github.com/fsantibanezleal/CAOS_SREVAL`. Its CHANGELOG records release 0.01.000
on 2026-07-22 and states that publishing to PyPI runs through OIDC trusted publishing with no stored
token. The package's own `__version__` is the `0.01.000` house format; PyPI carries the PEP 440 form
of the same release, `0.1.0`, uploaded 2026-07-22.

The git ref is gone from the manifest. [`requirements-precompute.txt`](../../requirements-precompute.txt)
now pins:

```
sreval[symbolic]==0.1.0
sympy==1.14.0            # required by sreval's symbolic equivalence test
```

One wrinkle a reader reproducing this build should know: the copy installed in this repo's `.venv`
was installed from the git ref before the release, so its `direct_url.json` records
`git+https://github.com/fsantibanezleal/CAOS_SREVAL@main` at commit `8b9af3b` while reporting version
0.1.0. A clean `pip install -r requirements-precompute.txt` resolves the same version from PyPI.

## Usage

```python
import numpy as np
from sreval import check, summarise

verdict = check(
    candidate_infix="x*(a + b)",
    truth_infix="x*a + x*b",
    variables=["x", "a", "b"],
    candidate_fn=lambda X: X[:, 0] * (X[:, 1] + X[:, 2]),
    truth_fn=lambda X: X[:, 0] * X[:, 1] + X[:, 0] * X[:, 2],
    box=[(-3.0, 3.0), (-3.0, 3.0), (-3.0, 3.0)],
    candidate_tokens=["mul", "v0", "add", "v1", "v2"],
    truth_tokens=["add", "mul", "v0", "v1", "mul", "v0", "v2"],
)

verdict.recovered            # True: an algebraic rewrite of the same expression
verdict.agreed               # True: the symbolic and numerical tests concur
verdict.structural.distance  # graded and non-zero: the two are written differently

report = summarise([verdict])
report.symbolic_failure_rate # the rate the field currently absorbs into method scores
```

## Applying it here

Stage 5 of the pipeline, [`data-pipeline/symlab/stages/evaluate.py`](../../data-pipeline/symlab/stages/evaluate.py),
imports it:

```python
from sreval import metrics as sreval_metrics
from sreval.equivalence import structural_distance as sreval_structural_distance
```

The import sits inside a `try` block that sets `HAS_SREVAL`, because the live (Pyodide) lane never
installs it and never needs it: the browser replays or reruns the search, and equivalence scoring is
an offline concern. The stage carries its own numerical probe constants
(`NUMERICAL_PROBE_POINTS = 512`, `NUMERICAL_TOLERANCE = 1e-6`, `ACCURACY_R2_THRESHOLD = 0.999`).

Exactly how much is delegated, stated precisely because this card once claimed more than was true:

| Test | Where it runs |
|---|---|
| Structural edit distance | `sreval.equivalence.structural_distance`, with the local loop kept as the browser-lane fallback |
| Symbolic | local, `sympy.simplify` on the difference, inside `stages/evaluate.py` |
| Numerical | local, a 512-point probe inside `stages/evaluate.py` |

So one of the three tests delegates today, not the protocol as a whole, and `sreval.equivalence`
carries `symbolic_equivalent`, `numerical_equivalent` and `check` that this repo does not call. The
second imported name in the snippet above, `sreval.metrics`, is bound and never referenced anywhere
in the module: it is the same unused-import shape this card was written to correct, at a smaller
scale, and it is recorded here rather than left for the next reader to find.

The package was extracted from this lab rather than written for it, for a licence reason as much as a
design one: the reference implementation of this protocol is SRBench's `symbolic_utils.py`, which is
GPL-3.0 and must not be vendored into an MIT product. Reimplementing from the published specification
is the route the research recorded, and `sreval` is that reimplementation.

## Caveats

- The structural distance is a sequence edit distance over the pre-order traversal, not a full tree
  edit distance. It is a graded signal, not a metric with the properties of Zhang-Shasha.
- `sreval` does not perform symbolic regression, and it does not decide whether a discovered equation
  is true. Fitting is not discovering, and no equivalence test changes that.
- The symbolic test needs the `symbolic` extra. Installed without it, the symbolic verdict is always
  "could not decide", which will inflate the reported symbolic failure rate for a reason that has
  nothing to do with the expressions.

## Citations

The protocol it implements is transcribed from the persisted benchmark research, primarily:

- La Cava, W., Orzechowski, P., Burlacu, B., de França, F. O., Virgolin, M., Jin, Y., Kommenda, M. and
  Moore, J. H. (2021). Contemporary Symbolic Regression Methods and their Relative Performance.
  NeurIPS 2021 Datasets and Benchmarks, arXiv:2107.14351. Source of the three-boolean equivalence
  rule and of `accuracy_solution = (R2_test > 0.999)`.
- Matsubara, Y., Chiba, N., Igarashi, R. and Ushiku, Y. Rethinking Symbolic Regression Datasets and
  Benchmarks for Scientific Discovery. arXiv:2206.10540. Source of the normalised tree edit distance
  as the graded alternative to a binary verdict.

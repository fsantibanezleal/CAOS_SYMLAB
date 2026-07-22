# Framework card, gplearn

**Status in this repo: SURVEYED, NOT USED.** This repo implements its own genetic-programming engine.
gplearn is the reference for what rung 1 of the ladder is supposed to be.

## What it is, and the one thing it does better

gplearn is the scikit-learn-flavoured, pure-Python implementation of Koza-style tree genetic
programming: ramped half-and-half initialisation, tournament selection, subtree crossover with
subtree, hoist and point mutation, protected operators, linear parsimony pressure, and `n_jobs`
parallelism over the offspring batch through joblib. Estimators are `SymbolicRegressor`,
`SymbolicClassifier` and `SymbolicTransformer`.

The one thing it does better than the alternatives is that it installs everywhere, including a
browser. It publishes a pure `gplearn-0.4.3-py3-none-any.whl` and its dependencies (numpy, scipy,
scikit-learn, joblib) all have Pyodide recipes, which makes it the only mature classical SR engine
that can be installed client-side through micropip. Everything faster is a native extension or a
Julia package.

## Licence, and whether this MIT repo may use it

BSD-3-Clause. Permissive, compatible with an MIT product, usable as a dependency or vendorable with
attribution. There is no licence obstacle to using it here; the reasons it is not used are technical.

## Install reality

`pip install gplearn`. Version 0.4.3 released 2026-01-07, which is the first release since 0.4.2 in
May 2022, so the project was dormant for over three years before that refresh. It now requires Python
>= 3.11 and scikit-learn >= 1.8.0. Repository last pushed 2026-01-10, 1871 stars. No compiler, no
GPU.

## Usage

```python
from gplearn.genetic import SymbolicRegressor

model = SymbolicRegressor(random_state=0)
model.fit(X_train, y_train)
print(model._program)
```

## Applying it here

Not used. This repo's engine is [`data-pipeline/symlab/search/engine.py`](../../data-pipeline/symlab/search/engine.py),
and `SearchConfig()` with no arguments is deliberately a faithful Koza-1992 baseline, which is the
same algorithm gplearn implements. It is entry `r1-koza-baseline` in the `LADDER` dictionary at the
bottom of that file. Three reasons the engine is in-house rather than a gplearn wrapper:

1. **The ladder has to be one engine.** Every later rung is a switch on the same `SearchConfig`, so
   that a measured difference is attributable to one named mechanism rather than to a change of
   library. An ablation across two codebases is not an ablation.
2. **The browser lane runs this engine, not a wheel.** The live worker
   ([`frontend/src/live/search.worker.ts`](../../frontend/src/live/search.worker.ts)) loads Pyodide
   0.28.3 and imports the same `symlab/model/` modules the offline bake ran, served from
   `public/engine/`. Nothing is downloaded from PyPI at runtime.
3. **Two of gplearn's design choices are the ones this lab argues against.** It has protected
   operators; this engine rejects with interval arithmetic instead
   ([`model/intervals.py`](../../data-pipeline/symlab/model/intervals.py), reasoning in
   [method-families/01_representation.md](../method-families/01_representation.md)). It has no
   constant optimisation beyond ephemeral random constants; this engine fits numeric leaves by
   Levenberg-Marquardt on a schedule ([`search/tune.py`](../../data-pipeline/symlab/search/tune.py)).

The honest comparison: on the mechanisms it implements, gplearn is mature, widely used and has years
of bug reports behind it, and this engine does not. What this engine has that gplearn does not is the
seven rungs above the baseline and a run that is a pure function of `(config, seed, data)`.

## Caveats

Transcribed from the persisted research, and the reason it is a baseline rather than a target:

- No constant optimisation (ephemeral random constants only), no linear scaling, no multi-objective
  front, no semantic operators, no interval arithmetic.
- Protected operators change the function being searched. The search never learns to avoid a
  singularity, and the model diverges the moment it is extrapolated.
- Consistently near the bottom in SRBench. Treat it as the reference classical Koza rung and as the
  browser-capable engine, never as the state of the art.
- `UNVERIFIED`: whether gplearn results are bit-identical across different `n_jobs` values. Test this
  before relying on it for a reproducible number.

## Citations

- Koza, J. R. (1992). Genetic Programming: On the Programming of Computers by Means of Natural
  Selection. MIT Press. The algorithm gplearn implements.
- Poli, R., Langdon, W. B. and McPhee, N. F. (2008). A Field Guide to Genetic Programming.
  gp-field-guide.org.uk. `UNVERIFIED`: exact ISBN.
- Documentation: gplearn.readthedocs.io; repository `github.com/trevorstephens/gplearn`. gplearn has
  no paper of its own; the research recorded its documentation as the citable source.

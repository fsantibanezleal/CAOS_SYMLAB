# Framework card, Operon and pyoperon

**Status in this repo: SURVEYED, NOT USED.** It is the throughput option, and this build has no
throughput problem yet.

## What it is, and the one thing it does better

Operon is a C++17 genetic-programming framework for symbolic regression, built for speed, with
pybind11 bindings published as `pyoperon`. Four design choices produce the speed, all verified from
the paper and the documentation site:

- **Linear tree encoding**: a program is a flat array of trivial `Node` structs (documented at 40
  bytes per node) traversed in postfix order. No pointer chasing, cache friendly.
- **Vectorized evaluation** through Eigen, so one tree is evaluated over a block of rows with SIMD.
- **Dual-number evaluation** in the same evaluator, giving exact forward-mode derivatives and
  therefore free gradients for Levenberg-Marquardt local search.
- **C++17 parallel execution policies** over the evolutionary loop, with minimal synchronisation.

Selection and survival cover GA, offspring-selection GA and NSGA-II variants.

The one thing it does better than the alternatives is runs per hour on a fixed CPU budget, under a
permissive licence, with prebuilt Windows wheels. When the task is a benchmark grid, an ablation or a
bootstrap confidence interval that needs thousands of runs, this is the engine.

## Licence, and whether this MIT repo may use it

MIT. Same licence as this repo. No obstacle to depending on it, vendoring it or forking it.

## Install reality

`pip install pyoperon`. Version 0.6.1 released 2026-03-01, with wheels for CPython 3.10 through 3.14
on `win_amd64`, manylinux x86_64 and macOS arm64 (macOS 14 and 15). Read from the PyPI API on
2026-07-22: there is no macOS x86_64 wheel, which an earlier version of this card claimed, so an
Intel Mac is a source build. The core repository was last pushed 2026-07-21, 211 stars.

That wheel matrix is a genuine advantage over FEAT, ellyn and GP-GOMEA, which are Linux-first source
builds. No GPU. Not Pyodide-safe: it is a native extension, so it cannot go in the browser lane.

## Usage

```python
from pyoperon.sklearn import SymbolicRegressor

model = SymbolicRegressor()
model.fit(X_train, y_train)
```

The sklearn wrapper supports callbacks, early stopping and `sample_weight`. Anything beyond the
wrapper means reading the C++: the README's documented build workflows are Linux and macOS, and the
readthedocs site states that the documentation is under construction.

## Applying it here

Not used. Nothing in this repo links against it or imports it.

The comparable code here is [`search/engine.py`](../../data-pipeline/symlab/search/engine.py), which
is a numpy tree engine, roughly the opposite end of the performance spectrum. The tradeoff is stated
rather than hidden: the measured cost of this build's rungs is published in
[method-families.md](../method-families.md) (0.30 s for the baseline, 6.73 s adding epsilon-lexicase,
0.75 s adding deduplication, 13.43 s adding both, at population 100 over 10 generations on 120 rows),
and those numbers are in the range where a Python engine is adequate and a C++ one would be an
optimisation without a question attached to it.

Two Operon ideas that are relevant to this build and are NOT implemented here:

- **Dual-number automatic differentiation** for the local search. This build's Levenberg-Marquardt in
  [`search/tune.py`](../../data-pipeline/symlab/search/tune.py) is hand-written on numpy, without
  autodiff.
- **Zobrist hashing with incremental updates**, so a mutated subtree updates its parent's hash in
  O(depth). Burlacu reports up to a 34% speedup in Operon from it (arXiv:2508.13859). This build
  deduplicates with a full canonical key plus a semantic hash on a row subsample
  (`canonical_key` and `semantic_key` in
  [`model/expr.py`](../../data-pipeline/symlab/model/expr.py)), recomputed rather than updated
  incrementally.

If this lab ever needs a benchmark grid rather than a demonstration, pyoperon is the first dependency
to add, and its MIT licence means there is nothing to resolve first.

## Caveats

- Large parameter surface, under-documented relative to PySR.
- No GPU, and not usable in the browser lane.
- `UNVERIFIED`: whether Operon runs are reproducible from a seed under parallel execution. It exposes
  a seed; whether parallel runs are bit-identical was not confirmed.
- The published quality claim is competitiveness with DEAP and HeuristicLab at significantly higher
  speed. The research recorded no transcribed runtime table, so no speed multiplier is quoted here.

## Citations

- Burlacu, B., Kronberger, G. and Kommenda, M. (2020). Operon C++: an efficient genetic programming
  framework for symbolic regression. GECCO 2020 Companion, pages 1562-1570,
  doi:10.1145/3377929.3398099.
- Burlacu, B. (2025). Zobrist Hash-based Duplicate Detection in Symbolic Regression.
  arXiv:2508.13859. Source of the 34% figure.
- Kommenda, M., Burlacu, B., Kronberger, G. and Affenzeller, M. (2020). Parameter identification for
  symbolic regression using nonlinear least squares. Genetic Programming and Evolvable Machines
  21:471-501, doi:10.1007/s10710-019-09371-3. The local-search method Operon's dual numbers feed.

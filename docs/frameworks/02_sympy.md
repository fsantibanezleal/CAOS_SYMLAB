# Framework card, SymPy

**Status in this repo: USED, indirectly.** It is pulled in by `sreval[symbolic]` for the symbolic
equivalence test. No module under `data-pipeline/symlab/` imports it.

## What it is, and the one thing it does better

SymPy is a computer algebra system in pure Python. In symbolic regression it is not a search engine,
it is the arbiter: it is the tool the whole benchmark literature uses to decide whether two
expressions are the same expression.

The one thing it does better than the alternatives is that it is the shared standard. SRBench's
equivalence check, the 2022 competition's scoring module and the SRSD edit-distance metric are all
built on it, so a result decided by SymPy is comparable with published results in a way that a
bespoke normaliser would not be.

## Licence, and whether this MIT repo may use it

BSD. Read from the installed distribution metadata in this repo's virtual environment
(`sympy-1.14.0.dist-info/METADATA`: `License: BSD`, classifier `License :: OSI Approved :: BSD
License`). Permissive, compatible with an MIT product, usable as a dependency without restriction.

## Install reality

`pip install sympy`. Pure Python, one dependency (`mpmath`). No compiler, no GPU. There is a Pyodide
recipe for it, so it is installable in a browser through micropip, which matters for any lab that
wants final simplification and LaTeX rendering client-side.

Pinned in this repo as `sympy>=1.12` in [`requirements-precompute.txt`](../../requirements-precompute.txt),
as a stated requirement of `sreval`'s symbolic test. The version resolved into the current
environment is 1.14.0.

## Usage

The calls that matter for SR evaluation are the ones SRBench's code uses, and they are worth naming
exactly because the details change the verdict:

```python
from sympy import simplify

# SRBench's rule, reproduced from experiment/symbolic_utils.py:
#   floats with |a| < 1e-4 become integer 0, everything else rounds to 3 decimals,
#   pi is replaced by the literal 3.1415926535, then:
simplified = simplify(model_sym, ratio=1)
```

`ratio=1` tells SymPy to accept a simplified form only if it is no larger than the input. The float
rounding happens before simplification, not after, because an unrounded fitted constant blocks
cancellation.

## Applying it here

Not directly. This repo's expression handling is its own: trees are built and walked in
[`data-pipeline/symlab/model/expr.py`](../../data-pipeline/symlab/model/expr.py), canonical and
semantic keys for deduplication live there (`canonical_key`, `semantic_key`), and LaTeX is generated
by [`model/latex.py`](../../data-pipeline/symlab/model/latex.py). The reasons are recorded in
[architecture/04_live-lane-pyodide.md](../architecture/04_live-lane-pyodide.md): the live lane loads
only `symlab/model/`, and every extra runtime dependency in that path is a download the browser has
to make before a search can start.

SymPy therefore appears in exactly one place in this build, as the engine behind `sreval`'s symbolic
verdict in [`stages/evaluate.py`](../../data-pipeline/symlab/stages/evaluate.py).

## Caveats

All four are transcribed from the persisted research and all four change reported numbers:

- `simplify` is a heuristic that tries many transformations and scores the results. Its cost is not
  predictable, which is why the 2022 SRBench competition wraps it in a 60 second alarm and why any
  pipeline using it must record timeouts as a distinct outcome rather than as a failure.
- SRBench 2.0 counts expression nodes on the sympy-converted but deliberately **unsimplified**
  expression, on the stated grounds that simplification is unreliable and can increase model size.
  A complexity number is therefore only comparable against another one measured the same way.
- `nsimplify` will turn 3.14159 into `pi`. That is what you want when presenting a discovered law and
  emphatically not what you want during a search.
- Full CAS simplification is safe as a post-processing step on a final Pareto front and is not safe
  inside an evolutionary inner loop. The cheap correctness-preserving rewrites (constant folding,
  `x + 0`, `x * 1`) are a different operation and should not be conflated with it.

## Citations

SymPy's role here is procedural rather than methodological, so the citations are the benchmark
sources that fix the protocol:

- La Cava, W. et al. (2021). Contemporary Symbolic Regression Methods and their Relative Performance.
  NeurIPS 2021 Datasets and Benchmarks, arXiv:2107.14351.
- Imai Aldeia, G. S., Zhang, H., Bomarito, G., Cranmer, M., Fonseca, A., Burlacu, B., La Cava, W. and
  de França, F. O. (2025). Call for Action: Towards the Next Generation of Symbolic Regression
  Benchmark. GECCO 2025 Symbolic Regression workshop, arXiv:2505.03977, doi:10.1145/3712255.3734309.
  Source of the unsimplified-node-count decision.

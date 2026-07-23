# Framework card, PhySO (Physical Symbolic Optimization)

**Status in this repo: SURVEYED, NOT USED.** The research recommended adopting it as a dependency
rather than reimplementing it; this build implements unit-typed generation itself, and the reason is
stated plainly below.

## What it is, and the one thing it does better

PhySO is a DSR-style reinforcement-learning generator, an RNN emitting expression tokens trained by
risk-seeking policy gradient, with one decisive addition: **dimensional analysis as an in-situ
constraint on the token distribution.** Every variable, constant and operator carries a units vector
over the physical dimensions. At each generation step the partially built tree determines what units
the next subtree must have, and every token whose units are inconsistent is **masked out of the
distribution before sampling**.

The paper's own framing is that the system is built from the ground up to propose solutions where the
physical units are consistent by construction, and that this is useful not only for eliminating
physically impossible solutions but because the grammatical rules of dimensional analysis enormously
restrict the freedom of the equation generator.

That second clause is the transferable part, and it generalises past physics to any typed grammar
(currency, counts, probabilities, log-scaled quantities): a hard constraint on the generator shrinks
the search space, where a soft penalty in the reward only re-ranks it.

The one thing it does better than the alternatives is symbolic recovery under noise on problems with
declared units: state-of-the-art performance on the Feynman benchmark in the presence of noise
exceeding 0.1%, robust at 10% noise. Note the careful scoping in that claim, which is the paper's own:
it is about the noisy regime, not the noiseless one.

**Class Symbolic Regression** (shipped in v1.1.0) is a second capability worth naming: fit multiple
datasets with a single shared analytical form but per-dataset free constants. That is the structure of
a real experimental campaign, same physics and different samples, and very few SR tools support it.

## Licence, and whether this MIT repo may use it

MIT (verified in the raw `LICENSE`, copyright Wassim Tenachi 2023). Compatible with this repo. There
is no licence obstacle.

## Install reality

`pip install physo`, also on conda-forge. Tested on Linux, macOS (ARM and Intel) and Windows, with
parallel execution modes and documentation at physo.readthedocs.io. Release history: 2023-03
initial, 2023-08 dimensional-analysis acceleration, 2024-02 uncertainty-aware fitting, 2024-05
Class SR, 2024-06 documentation overhaul. Read from the PyPI API on 2026-07-22, the current release
is 1.1.11, uploaded 2025-08-09, declaring `requires-python >= 3.8`. An earlier version of this card
said "Python 3.12+" and named 1.1.0 of 2024-06-14 as the current version; neither matches the
package metadata. A frozen v1.0.0 is archived on Zenodo at doi:10.5281/zenodo.8415435, which
resolves to "PhySO-v1.0.0", Zenodo, 2023.

Of all the physics-aware options in the research, this is the best engineered: a real package, a real
release history, real cross-platform testing, and a permissive licence.

## Usage

No snippet. The research verified the packaging and the mechanism but did not transcribe the API
surface, and a fabricated call would be worse than an omission. The documentation site is the source.

## Applying it here

Not used. The mechanism, however, is implemented independently in this build, and the honest
description of the relationship is that they share a principle and not an algorithm:

| | PhySO | Here |
|---|---|---|
| Generator | RNN policy trained by risk-seeking policy gradient | Ramped half-and-half plus subtree, point and hoist variation |
| Unit representation | units vector per token | seven-vector of SI base-dimension exponents, `Dims` in [`model/units.py`](../../data-pipeline/symlab/model/units.py) |
| Where units act | mask the token distribution before sampling | refuse to build a node whose units cannot work, `typed_population` in [`search/generate.py`](../../data-pipeline/symlab/search/generate.py) |
| Ladder position | the whole method | rung 8, `r8-unit-typed` in the `LADDER` of [`search/engine.py`](../../data-pipeline/symlab/search/engine.py) |

Three reasons the dependency was not taken despite the research's recommendation:

1. The ablation requires one engine. Rung 8 has to differ from rung 7 by exactly one switch, and a
   second engine with its own generator, its own selection and its own reward would make the
   comparison meaningless.
2. The live lane installs nothing beyond what the browser already has. The three packages it loads
   (`symlab/model/`, `symlab/search/`, `symlab/cases/`) import only the standard library and numpy,
   which is what lets the same modules run offline and under Pyodide.
3. This build has no reinforcement-learning component at all, so adopting PhySO would mean adopting a
   whole search paradigm, not a units feature.

What this build does NOT claim as a result: it is not a reimplementation of PhySO, it has no policy
network, and it has not been evaluated against PhySO on any shared benchmark. The units rung is cited
to PhySO's paper in [method-families/05_units.md](../method-families/05_units.md) for the principle,
not for the numbers.

## Caveats

- `UNVERIFIED`: PhySO's exact Feynman recovery rates per noise level, against DSR, gplearn and AI
  Feynman. The ar5iv rendering of the paper fails with a fatal LaTeX conversion error. The research
  recorded the route to close it: the IOP open-access PDF at
  `iopscience.iop.org/article/10.3847/1538-4357/ad014c/pdf` (CC BY). Do not quote per-noise numbers
  publicly before reading it.
- Unit consistency is a necessary condition for a physical law and never a sufficient one. A
  dimensionally perfect expression can still be the wrong law, which is the point of having an
  evaluation protocol at all.
- The method needs declared units. A case whose inputs carry no physical dimensions gets nothing from
  it, which is why this build omits the rung entirely on such cases rather than showing a control
  that silently does nothing.

## Citations

- Tenachi, W., Ibata, R. and Diakogiannis, F. I. (2023). Deep symbolic regression for physics guided
  by units constraints: toward the automated discovery of physical laws. The Astrophysical Journal
  959(2), 99, doi:10.3847/1538-4357/ad014c, arXiv:2303.03192.
- Tenachi, W. et al. (2023). Class Symbolic Regression: Gotta Fit 'Em All. arXiv:2312.01816.
- Frozen implementation archive: doi:10.5281/zenodo.8415435.

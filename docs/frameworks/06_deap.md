# Framework card, DEAP

**Status in this repo: SURVEYED, NOT USED.** The research recommended it as the substrate; this build
ships a self-contained engine instead, for reasons stated below.

## What it is, and the one thing it does better

DEAP (Distributed Evolutionary Algorithms in Python) is not a symbolic regression algorithm. It is
the toolbox most Python SR research code is built on: PS-Tree and EvolutionaryForest both sit on it.
Relevant modules, verified: `deap.gp` (primitive sets, typed primitive sets, `genHalfAndHalf`,
`cxOnePoint`, `mutUniform`, `staticLimit` depth-cap decorators), `deap.tools` (`selNSGA2`,
`selTournament`, `selSPEA2`, statistics, hall of fame) and `deap.algorithms` (`eaSimple`,
`eaMuPlusLambda`).

The one thing it does better than the alternatives is `gp.PrimitiveSetTyped`. Strongly typed genetic
programming is available directly, which is the mechanism that turns physical units into a type
system so that `+` requires matching units and `sin` requires a dimensionless argument. Most
frameworks make you build that yourself.

## Licence, and whether this MIT repo may use it

LGPL-3.0. It permits use as a library inside a non-GPL product; it constrains modification and
redistribution of DEAP itself. `UNVERIFIED`: the full legal reading for a closed or
differently-licensed product. The research flagged that explicitly as a legal question rather than a
code fact, and it is carried forward unresolved here.

For this repo the practical position is that depending on DEAP would have been permitted, and
vendoring or forking parts of it would have needed a legal answer that nobody has given.

## Install reality

`pip install deap`. Version 1.4.4 publishes a pure `deap-1.4.4-py3-none-any.whl` (93.1 kB) with no
platform-specific wheels for that version, so it is installable in Pyodide through micropip.
Repository last pushed 2026-04-17, 6420 stars. No compiler, no GPU.

## Usage

The API surface a symbolic-regression build actually touches, listed rather than assembled into a
program, because a full DEAP setup is several dozen lines of `toolbox.register` calls and the
authoritative version of it is in DEAP's own documentation:

| Need | DEAP entry point |
|---|---|
| Untyped primitive set | `deap.gp.PrimitiveSet` |
| Typed primitive set (units as types) | `deap.gp.PrimitiveSetTyped` |
| Ramped half-and-half initialisation | `deap.gp.genHalfAndHalf` |
| Subtree crossover, subtree mutation | `deap.gp.cxOnePoint`, `deap.gp.mutUniform` |
| Depth cap on the operators | `deap.gp.staticLimit` |
| Tournament, NSGA-II, SPEA2 survival | `deap.tools.selTournament`, `selNSGA2`, `selSPEA2` |
| Generational loops | `deap.algorithms.eaSimple`, `eaMuPlusLambda` |
| Parallelism | a user-provided `map` (multiprocessing, SCOOP) |

## Applying it here

Not used. Every one of those entry points has a counterpart written in this repo:

| DEAP | Here |
|---|---|
| `gp.genHalfAndHalf` | `ramped_half_and_half` in [`search/generate.py`](../../data-pipeline/symlab/search/generate.py) |
| `gp.cxOnePoint`, `gp.mutUniform` | `vary` in [`search/variation.py`](../../data-pipeline/symlab/search/variation.py) |
| `tools.selTournament`, `selNSGA2` | `tournament`, `nsga2_survival` in [`search/select.py`](../../data-pipeline/symlab/search/select.py) |
| `gp.PrimitiveSetTyped` | `typed_population` in `search/generate.py` over the SI dimension vectors in [`model/units.py`](../../data-pipeline/symlab/model/units.py) |
| user-provided `map` | none: the run is single-process by design |

The reasons are the same three that apply to gplearn, plus one specific to DEAP:

1. The whole ladder must live in one `SearchConfig` for the Experiments page to be an ablation.
2. The live lane copies `symlab/model/` into the browser and installs nothing.
3. Determinism is a contract here: a run is a pure function of `(config, seed, data)`, byte for byte.
   That is easier to hold when every source of randomness is one `numpy.random.default_rng(seed)`
   passed explicitly, which is not how DEAP's global-toolbox style works.
4. The LGPL question above has no answer on file, and the honest response to an unresolved licence
   question in a public product is to not take the dependency.

The search itself imports only the standard library and numpy: `symlab/model/`, `symlab/search/` and
`symlab/cases/`, which are exactly the packages copied into `frontend/public/engine/` for the browser.
The precompute-only modules add four third-party imports (`openpyxl` and `xlrd` in the loaders,
`sreval` and `sympy` in the evaluation stage), and none of them is on the path the live lane loads.
That split is a deliberate property, and it is what makes the offline engine and the browser engine
the same code.

## Caveats

- DEAP gives you machinery, not a method. Everything that separates a competent SR engine from a
  tutorial (linear scaling, constant fitting, interval guards, deduplication) is still yours to write.
- Its parallelism is whatever `map` you supply, so reproducibility across process counts is your
  problem, not DEAP's.

## Citations

- Fortin, F.-A., De Rainville, F.-M., Gardner, M.-A., Parizeau, M. and Gagné, C. (2012). DEAP:
  Evolutionary Algorithms Made Easy. Journal of Machine Learning Research 13:2171-2175.
- Montana, D. J. (1995). Strongly Typed Genetic Programming. Evolutionary Computation 3(2):199-230,
  doi:10.1162/evco.1995.3.2.199. The method behind `PrimitiveSetTyped`.

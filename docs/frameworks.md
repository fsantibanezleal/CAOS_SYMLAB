# Frameworks

One card per engine or library the research examined, with its licence, its install reality, and a
plain statement of whether this repo uses it or deliberately does not.

The rule this page enforces is that a card is not an endorsement. **This lab implements its own
search engine.** It does not wrap PySR, Operon, gplearn, DSO or any pretrained transformer, and no
card should be read as implying otherwise. Where a method is implemented here, the card says which
file implements it and how it differs from the reference. Where it is not, the card says why.

Every fact in these cards is transcribed from the persisted research dossiers, and anything the
research could not close against a primary source is carried forward marked `UNVERIFIED` rather than
quietly resolved.

## What this repo actually depends on

| Lane | File | Contents |
|---|---|---|
| Core and live | [`requirements.txt`](../requirements.txt) | `numpy==2.4.6`, and nothing else. Pyodide-safe by construction. |
| Precompute | [`requirements-precompute.txt`](../requirements-precompute.txt) | numpy, scipy, `openpyxl` and `xlrd` (two source datasets ship as spreadsheets), `sreval[symbolic]` and `sympy` |
| Dev | [`requirements-dev.txt`](../requirements-dev.txt) | `pytest`, `ruff` |
| API | [`requirements-api.txt`](../requirements-api.txt) | dormant, fully commented out |

The `symlab` package imports the standard library and numpy, and nothing else. `sreval` is imported
inside a `try` in [`stages/evaluate.py`](../data-pipeline/symlab/stages/evaluate.py) so the browser
lane runs without it. That is the whole third-party surface of this product.

Three discrepancies in the manifests, recorded rather than tidied:

- `scipy==1.16.3` is pinned in `requirements-precompute.txt` and no module under
  `data-pipeline/symlab/` imports it. The Levenberg-Marquardt tuner is hand-written on numpy in
  [`search/tune.py`](../data-pipeline/symlab/search/tune.py), which is what keeps the same code
  runnable under Pyodide.
- [`data-pipeline/requirements.txt`](../data-pipeline/requirements.txt) still carries the template's
  precompute-lane text and pins numpy alone, while the real precompute pins live in the root
  `requirements-precompute.txt`.
- There is no `requirements-gpu.txt`. This product has no GPU step, for the reasons in
  [22_evogp.md](frameworks/22_evogp.md) and [guides/03_gpu-lane.md](guides/03_gpu-lane.md).

## The cards

Status is one of: **used** here; **surveyed** and deliberately not used; **blocked**, meaning the
licence forbids use in an MIT product.

| Card | Family | Licence | Usable in an MIT repo | Status here |
|---|---|---|---|---|
| [01 sreval](frameworks/01_sreval.md) | Evaluation and equivalence | MIT | yes | **used**, in `stages/evaluate.py` |
| [02 SymPy](frameworks/02_sympy.md) | Computer algebra | BSD | yes | **used** indirectly, through `sreval[symbolic]` |
| [03 SRBench](frameworks/03_srbench.md) | Benchmark harness | GPL-3.0 | protocol yes, code no | protocol reimplemented in `sreval`; code never vendored |
| [04 PMLB](frameworks/04_pmlb.md) | Benchmark data | MIT | yes | surveyed; this lab builds its own case registry |
| [05 gplearn](frameworks/05_gplearn.md) | Koza tree GP | BSD-3-Clause | yes | surveyed; it is the reference for rung 1, which is implemented here |
| [06 DEAP](frameworks/06_deap.md) | EC substrate | LGPL-3.0 | as a library, with an open legal question | surveyed; the engine is self-contained instead |
| [07 PySR](frameworks/07_pysr.md) | Island GP, Julia backend | Apache-2.0 | yes | surveyed; not wrapped |
| [08 Operon](frameworks/08_operon.md) | High-throughput C++ GP | MIT | yes | surveyed; the first dependency to add if a benchmark grid is ever needed |
| [09 DSR / DSO](frameworks/09_dso.md) | RL-guided search | BSD-3-Clause | yes | surveyed; no RL rung exists here |
| [10 NeSymReS](frameworks/10_nesymres.md) | Pretrained transformer | MIT | yes | surveyed; no checkpoint is shipped or downloaded |
| [11 E2E](frameworks/11_e2e-transformer.md) | Pretrained transformer with constants | Apache 2.0 | yes | surveyed; repository archived read-only since 2023-10-31 |
| [12 TPSR](frameworks/12_tpsr.md) | MCTS decoding over a transformer | MIT | yes | surveyed; the shape a neural rung here should take if one is added |
| [13 AI Feynman](frameworks/13_ai-feynman.md) | Physics-aware decomposition | MIT | yes | surveyed; Linux or macOS only, needs a Fortran compiler |
| [14 PhySO](frameworks/14_physo.md) | Units as a generation constraint | MIT | yes | surveyed; the principle is implemented here independently as rung 8 |
| [15 PySINDy](frameworks/15_pysindy.md) | Sparse dictionary SR | MIT | yes | surveyed; a different problem class, no dynamics track here |
| [16 ODEFormer](frameworks/16_odeformer.md) | Transformer for ODE systems | MIT | yes | surveyed; ODEBench named as the benchmark to adopt if dynamics are added |
| [17 pykan](frameworks/17_pykan.md) | Spline network plus symbolic extraction | MIT | yes | surveyed; the symbolification step is the weak link |
| [18 ESR](frameworks/18_esr.md) | Exhaustive enumeration plus MDL | MIT | yes | surveyed; the rung is implemented here from the paper, with this build's own codelength |
| [19 FFX](frameworks/19_ffx.md) | Deterministic basis enumeration | non-OSI, non-commercial | **no** | blocked as a dependency; reimplementable, not yet reimplemented |
| [20 LLM-driven SR](frameworks/20_llm-sr.md) | Model as mutation operator | Apache 2.0 / MIT | yes | surveyed; an endpoint would break the determinism contract |
| [21 feyn / QLattice](frameworks/21_feyn-qlattice.md) | Proprietary graph search | CC-BY-NC-ND-4.0 | **no** | blocked; first on the SRBench++ synthetic track |
| [22 EvoGP](frameworks/22_evogp.md) | GPU tensorized tree GP | GPL-3.0 | **no** | blocked as a linked dependency; the GPU position statement lives here |

The card shape is [00_TEMPLATE.md](frameworks/00_TEMPLATE.md), extended with an explicit licence
heading because for a public MIT product the licence is a decision input, not a footnote.

## Surveyed and not carded

These appeared in the research with enough detail to be assessed and were not given a card, each for
a stated reason. None of them is used here.

| Method or package | Licence | Why no card |
|---|---|---|
| GP-GOMEA | Apache-2.0 | Linkage-learning GP, strong on size-constrained problems. Linux-first source build, no wheel, 57 stars. Its niche (best model at most N nodes) is covered here by the Pareto front plus bounded enumeration. |
| Semantic backpropagation GP (RDO, AGX) | via GP-GOMEA | SRBench identifies semantic search drivers as one of the two ingredients of the best methods, so this is the strongest omission in this build's ladder. It needs a precomputed semantic library indexed by semantics, which is a real piece of work rather than a switch. |
| FEAT | GPL-3.0 | Evolves networks of typed trees with a linear model on the evolved features. GPL, a heavy Shogun dependency (`UNVERIFIED` maintenance), no Windows wheels, PyPI release over four years old. |
| ITEA | BSD-3-Clause | Interaction-Transformation representation with OLS-exact weights, a genuinely different and smoother search landscape. Small package, last released mid-2023. A candidate rung, not a dependency. |
| ellyn / EPLEX | NOASSERTION | The epsilon-lexicase reference implementation. Unlicensed, unmaintained since 2022, not on PyPI. The selection method itself is implemented here (`epsilon_lexicase` in `search/select.py`). |
| MRGP | `UNVERIFIED` | Fits a linear model over the semantics of every subtree. Fast error reduction that destroys the interpretability symbolic regression exists for. Java, dormant. |
| PS-Tree, EvolutionaryForest, hal-cgp, PonyGE2, bingo, TiSR | MIT / LGPL-3.0 / GPL-3.0 / Apache-2.0 | Distinct mechanisms (piecewise SR, feature construction, Cartesian GP, grammatical evolution, MPI islands, thermodynamic constraints) with small communities. Recorded in the research; none is a dependency candidate for this build. |
| MINLP / ALAMO | commercial | The exact optimisation statement of what SR is, solved to global optimality by a commercial solver (BARON). Worth presenting as theory, not implementable here. |
| Bayesian Machine Scientist | `UNVERIFIED` | MCMC over expression trees with a prior estimated from Wikipedia expressions. The honest answer to "how confident are we", and the missing capability across all tree SR. Reference code only, licence `UNVERIFIED`. |
| Symbolic Physics Learner | MIT | MCTS over grammar productions. Notebook-based paper artifact, last pushed 2023. |
| EQL, EQL-div, OccamNet | `UNVERIFIED` / none | Neural equation learners. No maintained reference implementation was found for EQL, and OccamNet's repository shows no licence file, so it must be treated as all rights reserved until confirmed. |
| SNIP, MMSR, SymFormer, UniSymNet, ViSymRe, PhyE2E | MIT / `UNVERIFIED` | Transformer variants. SNIP is carded by reference inside [11_e2e-transformer.md](frameworks/11_e2e-transformer.md) because its contrastive latent space is the bridge to gradient-free search over expressions; the rest are recorded in the research and add nothing this build can act on. |

## What the research concluded, and what this build did with it

Three findings shaped the card set more than any individual engine:

- **There is no state of the art.** SRBench++ evaluated twelve modern methods and states that
  performance varies significantly by task type, preventing identification of a single best approach.
  Any claim here to implement "the SOTA" would be false, and none is made.
- **No method retrieves the correct expression free of irrelevant features.** Not one, in the whole
  benchmark. Extrapolation is subpar across the board. That is why this lab reports accuracy and
  recovery separately and never merges them ([docs/README.md](README.md)).
- **Decoding beats scale, and evaluation beats both for a lab this size.** The measured TPSR result
  (a frozen NeSymReS lifted from 0.635 to 0.808 accuracy at identical complexity, by changing only
  the decoding) says a search layer is worth more than a pretraining run. The evaluation gap, that
  nobody publishes the failure rate of their own equivalence scorer, is the one this build actually
  filled, in [`sreval`](frameworks/01_sreval.md).

# Framework card, DSR / DSO (deep symbolic optimization, including NGGP and uDSR)

**Status in this repo: SURVEYED, NOT USED.** No reinforcement-learning rung exists in this build.

## What it is, and the one thing it does better

Deep Symbolic Regression frames expression discovery as sequence generation. An autoregressive RNN
emits a distribution over pre-order traversals of expression trees, token by token, with constraints
applied in situ by masking the logits (forbid `log` directly inside `exp`, enforce arity, cap
length). Each sampled traversal becomes an expression, its constants are fit, and it receives a
reward such as

    R(tau) = 1 / (1 + NRMSE(tau))

The one thing it does better than the alternatives is the **risk-seeking policy gradient**. Standard
REINFORCE optimises expected reward, which is the wrong objective: in symbolic regression nobody
cares about the average sampled expression, only about the best one. DSR optimises the upper tail.
With `R_eps(theta)` the `(1 - eps)` quantile of the reward distribution under the current policy:

    grad J_risk(theta; eps)
      = E[ ( R(tau) - R_eps(theta) ) * grad log p(tau | theta)  |  R(tau) >= R_eps(theta) ]

estimated by sampling a batch, keeping the top `eps` fraction, and applying the policy gradient to
those alone.

Two descendants ship in the same repository:

- **NGGP** (neural-guided genetic programming): the RNN's samples seed the initial population of a
  genetic-programming run, the GP improves them, and the best GP results train the RNN. It recovers
  65% more expressions than the previous top-performing model, and its useful engineering finding is
  that keeping the neural and GP components **loosely coupled** works better than tight integration.
- **uDSR**: the unification, integrating five solution strategies (recursive problem simplification,
  neural-guided search, large-scale pre-training, genetic programming, and linear models entering as
  the `poly` or LINEAR token, a leaf standing for "a linear model fitted in closed form here").

## Licence, and whether this MIT repo may use it

BSD-3-Clause (`dso-org/deep-symbolic-optimization`, verified on the repository page). Permissive and
compatible with an MIT product. The obstacle is the stack, not the licence.

## Install reality

Source install. Latest release v3.0.0 dated 2023-03-11; repository last pushed 2026-01-23, 735 stars.
TensorFlow-based, Python 3.6+, tested on Unix and macOS, and it ships **no pretrained weights**. The
research recorded it as the component least likely to install cleanly on Windows.

The README points to a modern PyTorch refactor. `UNVERIFIED`: which repository that is.

## Usage

No API snippet is reproduced here, because none was transcribed from a primary source in the research
and inventing one would be worse than omitting it. What was transcribed is the mechanism above, which
is what a reimplementation needs; the research estimated the risk-seeking loop at roughly 300 lines.

## Applying it here

Not used, and not reimplemented. This build's ladder is the classical spine (representation, scaling,
constant fitting, selection and survival, deduplication, unit typing) plus bounded exhaustive search.
There is no policy network anywhere in
[`data-pipeline/symlab/`](../../data-pipeline/symlab/), no TensorFlow or PyTorch dependency, and no
learned proposal distribution. The `models/` directory holds one file, `surrogate.json`, which is a
four-term linear least-squares surrogate, not a neural model.

One DSR idea is present in a different form and should be named as a parallel rather than an
implementation: **constrain generation rather than filter afterwards**. DSR masks tokens whose arity
or nesting would be invalid before sampling; this build masks tokens whose physical units cannot work
before building the node, in `typed_population` in
[`search/generate.py`](../../data-pipeline/symlab/search/generate.py) over the SI dimension vectors
in [`model/units.py`](../../data-pipeline/symlab/model/units.py). The principle is the same and the
constraint is not: dimensions instead of syntax.

The `poly` token idea (let linear algebra solve what evolution should not have to) also has a much
smaller cousin here in Keijzer linear scaling
([`model/scaling.py`](../../data-pipeline/symlab/model/scaling.py)), which solves only the outermost
multiplicative and additive constants in closed form.

## Caveats

- The reference implementation of the most-cited neural SR method sits on an ageing TensorFlow stack
  with heavy dependencies. Its ideas are more valuable to a small lab than its code.
- `UNVERIFIED`: uDSR's exact SRBench symbolic and accuracy solution rates. The NeurIPS PDF could not
  be parsed in the research session. What is verified independently is that SRBench++ ranked uDSR
  **third** on the synthetic track and **first** on the real-world COVID-19 track with score 5.75.
- The same repository ships the Livermore, R, Jin and Constant benchmark sets as
  `dso/dso/task/regression/benchmarks.csv` (BSD-3-Clause). A comparability trap lives there: the CSV
  keeps Nguyen-2, Nguyen-11 and Nguyen-12, which the corrected v3 Table 3 of McDermott et al. omits,
  and it samples Nguyen-9 through Nguyen-12 on `U[0, 1, 20]` where the corrected table uses
  `U[-1, 1, 100]`. Two papers reporting a "Nguyen recovery rate" are not necessarily comparable.

## Citations

- Petersen, B. K., Landajuela, M., Mundhenk, T. N., Santiago, C. P., Kim, S. K. and Kim, J. T. (2021).
  Deep symbolic regression: recovering mathematical expressions from data via risk-seeking policy
  gradients. ICLR 2021, arXiv:1912.04871.
- Mundhenk, T. N., Landajuela, M., Glatt, R., Santiago, C. P., Faissol, D. M. and Petersen, B. K.
  (2021). Symbolic Regression via Neural-Guided Genetic Programming Population Seeding. NeurIPS 2021,
  arXiv:2111.00053.
- Landajuela, M., Lee, C. S., Yang, J., Glatt, R., Santiago, C. P., Aravena, I., Mundhenk, T. N.,
  Mulcahy, G. and Petersen, B. K. (2022). A Unified Framework for Deep Symbolic Regression.
  NeurIPS 2022.
- McDermott, J. et al. (2012). Genetic Programming Needs Better Benchmarks. GECCO 2012,
  doi:10.1145/2330163.2330273. Source of the corrected Nguyen table.

# Framework card, PySR and SymbolicRegression.jl

**Status in this repo: SURVEYED, NOT USED.** It is the strongest general-purpose open SR engine the
research found, and this repo does not wrap it.

## What it is, and the one thing it does better

PySR is a scikit-learn compatible Python front end over SymbolicRegression.jl, a multi-population
(island) evolutionary SR engine written in Julia. Three documented specialisations over classic
genetic programming:

1. **Simulated annealing inside the island tournament.** A mutated expression is accepted with
   probability `p = exp(-dL / T)` for a temperature annealed over the cycle, so uphill moves are
   sometimes accepted and an island can leave a local minimum.
2. **The evolve-simplify-optimize loop.** Each cycle mutates, then analytically simplifies equivalent
   expressions, then optimises the numeric constants. The simplification step between mutation and
   constant fitting is what stops the optimiser wasting effort on redundant parameterisations.
3. **Adaptive parsimony.** Instead of one complexity penalty, it maintains a good population at
   *every* complexity, so small models are never crowded out.

The output is a hall of fame that is a Pareto front over complexity, with migration between
populations and from the hall of fame.

The one thing it does better than the alternatives is breadth of real scientific use: custom
operators, custom Julia losses, dimensional-analysis constraints, and export to SymPy, JAX and
PyTorch for downstream use, in a package that installs natively on Windows, Linux and macOS. It
ranked second on the SRBench++ synthetic track and is one of only four methods (with uDSR, Operon and
Bingo) that found exact solutions in the 2022 competition.

## Licence, and whether this MIT repo may use it

Apache-2.0, permissive and compatible with an MIT product. Recorded caveat on the provenance of that
fact: the classical-GP research pass verified it from the package and repository metadata, while the
neural and benchmark passes both marked PySR's licence `UNVERIFIED` because they did not fetch the
`LICENSE` file in their own sessions. The classical pass is the primary source used here.

## Install reality

`pip install pysr`, which installs Julia automatically, or `conda install -c conda-forge pysr`. PySR
1.5.10 released 2026-03-30 with a 2.0.0a2 pre-release on 2026-05-16; SymbolicRegression.jl v1.13.2 on
2026-03-29 with v2.0.0-alpha.11 on 2026-05-17. Repository last pushed 2026-07-20, 3631 stars (801 on
the Julia package).

The friction is the Julia environment: the first import compiles it, which is a multi-minute one-time
cost and a real problem in CI and in containers. It cannot run in a browser. There is no GPU search
path; PySR's GPU story is export to JAX or PyTorch for downstream inference.

## Usage

Verified defaults from the `PySRRegressor` docstring, which are worth reading before quoting any PySR
result:

```python
from pysr import PySRRegressor

model = PySRRegressor(
    binary_operators=["+", "-", "*", "/"],   # unary_operators=None by default
    niterations=100,
    populations=31,
    population_size=27,
    maxsize=30,
    parsimony=0.0,
    model_selection="best",
    elementwise_loss="L2DistLoss()",
    optimizer_algorithm="BFGS",              # optimizer_iterations=8
    batching="auto",                         # enabled for n > 1000
    parallelism="serial",                    # required for determinism
    deterministic=True,
    random_state=0,
)
model.fit(X, y)
```

**Determinism is the operational fact a lab must know.** Verified from the docstring:
`deterministic=True` requires `parallelism="serial"` AND a fixed `random_state`. There is no
deterministic parallel mode. Reproducible PySR runs are single-threaded.

## Applying it here

Not used, and not wrapped. Nothing in this repo imports, shells out to, or embeds PySR. Two reasons:

1. **The artifact contract.** Every number in this product is replayed from a seeded offline run and
   must regenerate byte for byte ([architecture/02_determinism-and-trace.md](../architecture/02_determinism-and-trace.md)).
   PySR offers that only single-threaded, which removes the throughput advantage that is the reason
   to use it.
2. **The live lane.** The browser runs the same engine as the bake, under Pyodide. Julia cannot go
   there, so adopting PySR would have meant two engines and a parity problem to test forever.

The mechanisms overlap honestly rather than completely. This repo's engine has islands with
migration, multi-objective survival on (loss, complexity), linear scaling and Levenberg-Marquardt
constant tuning, all in [`search/engine.py`](../../data-pipeline/symlab/search/engine.py). It does
not have simulated-annealing acceptance, adaptive parsimony across complexities, Julia throughput, or
anything like PySR's maturity. Those are absences, and they are stated as absences.

## Caveats

- `constraints` and `nested_constraints` are essential on transcendental operator sets and are OFF by
  default, so a naive run produces `sin(sin(sin(x)))` output.
- The first-import Julia compilation is a genuine barrier in automated environments.
- `UNVERIFIED`: whether the 2.0 alpha line adds any GPU evaluation path to the search.
- `UNVERIFIED`: PySR's exact parameter name for dimensional-analysis constraints. The capability is
  documented at the API level; the name was not re-read.

## Citations

- Cranmer, M. (2023). Interpretable Machine Learning for Science with PySR and
  SymbolicRegression.jl. arXiv:2305.01582.
- de França, F. O., Virgolin, M., Kommenda, M. et al. (2024). SRBench++. IEEE Transactions on
  Evolutionary Computation, doi:10.1109/TEVC.2024.3423681. Source of the synthetic-track ranking.
- de França, F. O. et al. (2023). Interpretable Symbolic Regression for Data Science: Analysis of the
  2022 Competition. arXiv:2304.01117. Source of the exact-solution finding.

PySR also ships **EmpiricalBench**, an evaluation of recovery of historical empirical equations from
original and synthetic datasets (described in arXiv:2305.01582). The research recorded it as a better
proxy for real discovery than rediscovering the Feynman set, and it is the benchmark this lab would
adopt first if it added an external one.

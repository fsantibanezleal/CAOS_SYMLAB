# Framework card, feyn and the QLattice

**Status in this repo: SURVEYED, LICENCE BLOCKED.** It is the strongest engine in the benchmark
tables that this repo may not use, and that is why it has a card.

## What it is, and the one thing it does better

The QLattice is Abzu's proprietary search engine, exposed through the `feyn` Python package. It
explores models as interpretable mathematical equation **graphs** and is described by its authors as
inspired by the path-integral formulation. It is a proprietary simulator rather than a published
genetic-programming algorithm, so it is GP-adjacent rather than GP.

The one thing it does better than the alternatives, on the published evidence, is aggregate
benchmark performance on synthetic problems: **SRBench++ ranked QLattice first on the synthetic
track** (ahead of PySR and uDSR) and second on the real-world COVID-19 track with score 5.21. In a
field where the benchmark authors state there is no dominant method, that is as close to a top rank
as anything gets.

## Licence, and whether this MIT repo may use it

**No.** PyPI reports `feyn` 3.5.0 under **CC-BY-NC-ND-4.0**: non-commercial **and** no-derivatives.
A public product cannot depend on it, cannot redistribute it, and cannot present it as part of an
open ladder. The engine behind it is closed in any case.

This card exists to state that plainly rather than to leave a reader wondering why the top-ranked
synthetic-track method is missing from a lab that surveys the field.

## Install reality

`pip install feyn`. Version 3.5.0. `UNVERIFIED`: GPU support. The install is not the obstacle; the
licence is.

## Usage

Not reproduced, for the same reason as FFX: this repo has decided it may not use the package, and a
usage snippet would invite installing it.

## Applying it here

Not used and not usable. Nothing in this repo depends on it, and nothing should.

The consequence for how this lab reports results is worth stating: any comparison table that ranks
open engines and omits QLattice is not a picture of the field, it is a picture of the permissively
licensed part of the field. Where SRBench++ rankings are quoted anywhere in this documentation, the
QLattice result is quoted with them.

## Caveats

- The engine is closed, so the mechanism cannot be inspected, reimplemented or audited. A benchmark
  rank for a closed engine is a measurement of a product, not of a method.
- `UNVERIFIED`: `feyn` GPU support.

## Citations

- Broløs, K. R. et al. (2021). An Approach to Symbolic Regression Using Feyn. arXiv:2104.05417.
- de França, F. O., Virgolin, M., Kommenda, M. et al. (2024). SRBench++: Principled Benchmarking of
  Symbolic Regression With Domain-Expert Interpretation. IEEE Transactions on Evolutionary
  Computation, doi:10.1109/TEVC.2024.3423681. Source of both rankings quoted above.

## A related historical note: Eureqa

Eureqa was the Schmidt and Lipson engine from Cornell: age-fitness Pareto survival, an
accuracy-complexity front, and a derivative-based fitness for dynamical systems. Nutonian was
acquired by DataRobot in 2017, the standalone product was discontinued, and the technology was folded
into the DataRobot platform. It is not obtainable as software today and survives in the literature
mainly as a baseline that newer methods report beating.

Its algorithm, unlike the QLattice's, is published, and one part of it is worth reimplementing rather
than citing: its fitness for dynamical systems compares **partial derivative ratios** estimated
numerically from the data against those computed symbolically from the candidate, which is what let
it find conservation laws (invariants) rather than input-output maps. This build implements the
age-fitness Pareto survival half of the Eureqa recipe (`age_fitness_survival` in
[`search/select.py`](../../data-pipeline/symlab/search/select.py), rung 6 of the ladder) and does not
implement the derivative-ratio fitness, which would need a dynamics track.

- Schmidt, M. and Lipson, H. (2009). Distilling Free-Form Natural Laws from Experimental Data.
  Science 324(5923):81-85, doi:10.1126/science.1165893.
- Schmidt, M. and Lipson, H. (2011). Age-Fitness Pareto Optimization. Genetic Programming Theory and
  Practice VIII, chapter 8, pages 129-146, doi:10.1007/978-1-4419-7747-2_8.

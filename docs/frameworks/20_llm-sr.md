# Framework card, LLM-driven SR (FunSearch, LLM-SR, LLM-SRBench)

**Status in this repo: SURVEYED, NOT USED.** No language model is called anywhere in this pipeline,
and calling one would break the determinism contract by construction.

## What it is, and the one thing it does better

The family shares one architecture, set by **FunSearch**: an evolutionary loop where the mutation
operator is a language model. A population of programs is scored by a **deterministic automated
evaluator**, the model is prompted with a few high-scoring programs and asked to write a better one,
and nothing is trusted: every candidate is executed and scored. FunSearch's own framing is that it
searches for programs describing **how** to solve a problem rather than **what** the solution is. It
produced new constructions for the cap set problem in dimension 8 and improved heuristics for online
bin packing.

**LLM-SR** applies that pattern to scientific equation discovery with two commitments: equations are
represented as **programs** (a Python function skeleton with free parameters) rather than as
expression trees, and the model proposes hypotheses grounded in scientific domain knowledge it
already has, with the parameters then fit by a numerical optimiser.

The one thing this family does better than the alternatives is **out-of-domain behaviour on problems
with a scientific literature behind them**. LLM-SR reports discovering physically accurate equations
that significantly outperform state-of-the-art symbolic regression baselines, particularly in
out-of-domain test settings. In-context SR, the minimal member of the family with no evolutionary
machinery at all, reports equations that are simpler and generalise better out of distribution than
the best SR baselines.

## Licence, and whether this MIT repo may use it

- **FunSearch**: Apache 2.0 for the code plus CC-BY 4.0 for other materials, verified. Permissive.
- **LLM-SR**: MIT, verified. Permissive.
- **LLM-SRBench**: the README states MIT; `UNVERIFIED`, no `LICENSE` file was returned by the GitHub
  licence endpoint.

None of these licences is the reason the family is unused here.

## Install reality

The honest statement about FunSearch first, because it is routinely misdescribed: the repository
contains the discovered artifacts (cap sets, admissible sets, bin-packing heuristics, cyclic graphs)
plus a single-threaded illustrative implementation in Jupyter notebooks, and it **explicitly does not
contain the language models, the sandbox for executing untrusted code, or the distributed
infrastructure**. Anyone claiming to run FunSearch is running a reimplementation.

LLM-SR is a source checkout that needs an inference endpoint. It supports a local
`mistralai/Mixtral-8x7B-Instruct-v0.1` with 4-bit and 8-bit quantization, or OpenAI `gpt-3.5-turbo`
and `gpt-4o`. A GPU is needed to serve the local model; VRAM figures are not documented. Its four
benchmark problems are `oscillator1`, `oscillator2`, `bactgrow` and `stressstrain`, and its README
gives no numerical results.

## Usage

No snippet. The research read these at the level of mechanism and repository contents, not calling
convention.

## Applying it here

Not used, and the reason is structural rather than a preference.

A run in this build is a pure function of `(config, seed, data)`, and the same inputs must give the
same Pareto front byte for byte, because every number in the app is replayed from a committed
artifact (the contract is stated in
[`search/engine.py`](../../data-pipeline/symlab/search/engine.py) and in
[architecture/02_determinism-and-trace.md](../architecture/02_determinism-and-trace.md)). A hosted
model endpoint has a version, a temperature, a sampling seed the caller does not control, and a model
that can be silently replaced. Adding one would end the contract. A locally served open-weights model
would be a partial answer and is still a multi-gigabyte dependency with no place in a lane that runs
under Pyodide.

## Caveats

These four are stated at length because published headline numbers in this family are systematically
inflated without them.

1. **Contamination is the central problem, and it is measured.** LLM-SRBench exists because existing
   benchmarks rely on common equations susceptible to memorization by language models, giving inflated
   metrics that do not reflect discovery. Its design is anti-contamination: LSR-Transform rewrites
   common physical models into less common mathematical representations, and LSR-Synth builds
   synthetic discovery-driven problems. 239 problems across four scientific domains, being 111
   LSR-Transform and 128 LSR-Synth. **The verified headline result is that the best-performing system
   achieves only 31.5% symbolic accuracy.** A product reporting high Feynman recovery from a
   language-model method and not reporting LLM-SRBench is reporting memorization.
2. **Reproducibility.** Results depend on a model endpoint whose version, temperature and sampling
   are outside the researcher's control for closed models. LLM-SR mitigates this by supporting a
   local Mixtral, which is the configuration a serious lab should default to.
3. **Cost.** Every candidate expression is a generation. `UNVERIFIED`: neither FunSearch's nor
   LLM-SR's public materials give a cost per discovered equation.
4. **The evaluator is doing the work.** In FunSearch, LLM-SR and LaSR alike, correctness is enforced
   by a deterministic external evaluator, not by the model. The model is a proposal distribution with
   good priors. Describing this as "the AI discovered the law" misrepresents the architecture.

The 2026 agentic wave extends the pattern rather than changing it: SR-Scientist promotes the model
from proposer to agent that writes analysis code, implements the equation, submits it for evaluation
and optimises on feedback, reporting absolute margins of 6% to 35% over baselines (`UNVERIFIED`:
which models were used). An instructive ablation in the same wave has the language model set only the
**search parameters** while a conventional symbolic regressor does the enumerating (arXiv:2607.04156,
`UNVERIFIED` beyond the title); if that works as well as full model-in-the-loop, much of this
literature is over-engineered.

## Citations

- Romera-Paredes, B., Barekatain, M., Novikov, A., Balog, M., Kumar, M. P., Dupont, E., Ruiz, F. J. R.,
  Ellenberg, J. S., Wang, P., Fawzi, O., Kohli, P. and Fawzi, A. (2024). Mathematical discoveries from
  program search with large language models. Nature 625:468-475, doi:10.1038/s41586-023-06924-6.
- Shojaee, P., Meidani, K., Gupta, S., Barati Farimani, A. and Reddy, C. K. (2025). LLM-SR: Scientific
  Equation Discovery via Programming with Large Language Models. ICLR 2025 Oral, arXiv:2404.18400.
- Shojaee, P., Nguyen, N.-H., Meidani, K., Barati Farimani, A., Doan, K. D. and Reddy, C. K. (2025).
  LLM-SRBench: A New Benchmark for Scientific Equation Discovery with Large Language Models.
  ICML 2025 Oral, arXiv:2504.10415.
- Merler, M., Haitsiukevich, K., Dainese, N. and Marttinen, P. (2024). In-Context Symbolic Regression.
  ACL Student Research Workshop 2024, doi:10.18653/v1/2024.acl-srw.49, arXiv:2404.19094.
- Grayeli, A., Sehgal, A., Costilla-Reyes, O., Cranmer, M. and Chaudhuri, S. (2024). Symbolic
  Regression with a Learned Concept Library (LaSR). NeurIPS 2024, arXiv:2409.09359.
- Xia, H., Sun, Q. and Liu, W. (2026). SR-Scientist. ICLR 2026, arXiv:2510.11661.

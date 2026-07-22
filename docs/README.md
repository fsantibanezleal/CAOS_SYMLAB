# Docs, the product wiki

A navigable wiki (ADR-0056), authored **as the product is built** rather than at the end. The pipeline, its
validation and these pages are the primary product; the web app is a projection of a validated subset of them.

SymLab is a research lab for **symbolic regression**: recovering an explicit closed-form expression from data,
rather than fitting an opaque predictor. The argument the whole product is built around is that accuracy and
recovery are different claims, and that a method can clear R2 > 0.999 while returning the wrong structure. So
this lab reports the two separately, always, and never merges them into one success rate.

## Map

- **[architecture/](architecture/)**, how the repo works: the frozen base, the two data contracts, determinism
  and trace, the live/precompute gate, the staged pipeline, model evaluation, deploy.
- **[method-families/](method-families/)**, the deep method pages: representation, scaling and constant fitting,
  selection and survival, deduplication, dimensional typing, bounded exhaustive search, and sparse regression
  over a fixed basis. Each carries the theory, the equations and the citations behind one mechanism. The first
  six sit inside the genetic-programming ladder; the seventh is the NON-evolutionary family, and calling it a
  rung would repeat exactly the conflation this lab is built to avoid, since a ladder of GP rungs alone is an
  ablation of GP rather than a survey of the field.
- **[frameworks/](frameworks/)**, one card per engine or library the research examined: what it is, its licence,
  its install reality, and whether this repo uses it or deliberately does not.
- **[guides/](guides/)**, runnable how-tos: read the workbench, run the precompute pipeline, bring your own data,
  the GPU lane, run the API, the in-app architecture modal.
- **[cases/](cases/)**, the category taxonomy, the coverage matrix, and one page per case: what the quantity is,
  whether a published law exists, the recovery regime, the provenance and the defects the loader applies.

## The two measurements, and why they are never merged

| Reported as | Means | Reported when |
|---|---|---|
| accuracy solution | a configuration cleared the accuracy threshold on held-out rows | every case |
| exact recovery | the returned expression is equivalent to the published law | ONLY where a law exists |

A case with no published closed form (a plant or instrument dataset) contributes to the error metrics and to no
recovery rate. Reporting it as zero recovery would be a false statement about the method, so the app and these
pages say "not checkable" instead.

Where a law does exist, the **recovery regime** is stated, because two different claims otherwise hide under one
word. "structure" means the physical parameters were supplied as input columns, so only the FORM was unknown:
that is the convention the published physics benchmarks use. "structure+constants" means the numbers had to be
recovered as well, which is materially harder.

Equivalence is decided by three tests that can disagree: symbolic (through sympy), numerical (probing a box of
inputs), and structural (a normalised edit distance). Disagreement is published rather than resolved silently,
because the symbolic and numerical tests usually agree inside the sampled box and differ outside it, which is
exactly where a wrong expression gives itself away.

## Honesty and data policy

- Numbers come from the committed artifacts, never from a claim. Every figure in the app is replayed from a
  seeded offline run. The live lane loads the same engine modules into the browser at a reduced budget, on
  data it generates there from a registered generator, so it corroborates the engine rather than the case:
  16 of the 25 registry cases have such a generator, and the measured-data cases have none.
- Public derived artifacts are committed (`data/derived/`); raw sources stay out of git (the download vault is
  outside the repository, see `io/sources.py`) per ADR-0055. The two data contracts
  ([architecture/08_data-contracts.md](architecture/08_data-contracts.md)) govern raw to pipeline and pipeline
  to web.
- Source defects are recorded verbatim rather than tidied away: rows dropped, folds ignored, aggregation
  applied, a comma decimal separator inside quoted fields, and the guard that rejects a Git LFS pointer served
  with HTTP 200. Two entries in `io/sources.py` carry recorded defects (the OpenML flotation dataset and the
  UCI water treatment plant), and the failures the research hit split two ways: the flotation file id and the
  PMLB raw route both answered HTTP 200 with the wrong bytes, while the Princeton host cited for the Nikuradse
  measurements answered HTTP 404. A status code decides nothing; only reading the content does.

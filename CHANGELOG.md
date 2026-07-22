# Changelog

All notable changes are documented here. Format follows Keep a Changelog; newest on top.
Version format is X.XX.XXX; the manifest carries the semver form with zeros dropped.

## 0.04.000 - 2026-07-22

The version this lab starts actually taking its own headline measurement, and the measurement
immediately shows the gap the product was built to show. On the re-baked Feynman cases:

| Case | Law | Accuracy | Recovery | Structural distance |
|---|---|---|---|---|
| I.12.1 | F = mu*Nn | 8/8 | 8/8 | 0.000 |
| I.12.5 | F = q2*Ef | 8/8 | 8/8 | 0.000 |
| I.6.2a | Gaussian | 5/8 | 0/8 | 0.788 |

Five of eight configurations cleared the accuracy threshold on the Gaussian and none recovered the
structure. The symbolic test failure rate on that case is 0.0, so the zero is a real result rather
than a scorer that could not decide, which is exactly why that rate is published separately.

### Added

- **Recovery scoring, which had never run.** `pipeline.py` passed `truth=None` to the evaluator at
  both call sites, so the triple-equivalence test never executed and `exact_recovery_rate` was
  `null` on every case ever baked. The gap between clearing an accuracy threshold and recovering
  the law is the measurement this product is built around, and it was not being taken. The truth is
  now resolved per case, carried on `PreparedCase`, and handed to the evaluator and the export. The
  search still never receives it.
- **35 verified truth expressions.** 17 of 18 generators, 17 of 18 selected Feynman laws, and one
  measured identity. Every one is checked against its own data before it is allowed to score,
  because a wrong truth does not fail loudly: it publishes a confident "not recovered" against a
  method that recovered the law perfectly.
- **A recovery REGIME on every scoreable case.** "structure" means the physical parameters were
  input columns so only the form was unknown, which is the convention the published physics
  benchmarks use; "structure+constants" means the numbers had to be found too. Two materially
  different claims previously wore the same word.
- **Full row accounting** in the artifact: source, used, train, test, extrapolation. `n_rows` alone
  is the TRAINING count and contradicted the case description on every subsampled case, so the app
  showed "2 550 rows" under a description reading "9,568 hourly records".
- **The wiki pages that were promised and absent**: 22 framework cards with licence and
  MIT-compatibility per row, and one page per case for all 25.
- **`docs/guides/00_read-the-workbench.md`**, which says what every control does and what every
  panel CLAIMS.
- Spanish category names in the registry, so the taxonomy is bilingual at its source rather than
  translated in the frontend where a second copy would drift.

### Changed

- **The App is a comparison, not a display.** The Expression tab puts what the search FOUND beside
  the relationship we EXPECTED, each labelled above its own mathematics, with the equivalence
  verdict between them. A reader previously had no way to tell the result from the input, and that
  distinction is the entire claim of the product.
- Six tabs in reading order: Expression, Structure, Parity and residuals, Live, Front and search,
  Context. Parity, residuals per input, extrapolation and partial dependence were previously
  stacked underneath the equation.
- **Residuals against each input**, a view that was missing entirely. It is where a missing term
  shows and where a parity plot hides it.
- The case navigator is three dropdowns (source, category, case) rather than a chip deck. Twenty-five
  cases across six categories do not fit a deck in a sidebar column.
- The manifests describe the real install: `scipy` removed (pinned for months, never installed,
  never imported), numpy and ruff aligned to the verified versions, `sreval` moved from a git ref to
  the published `0.1.0`, and `data-pipeline/requirements.txt` reduced to a pointer, because two
  files claiming one lane is how a pin drifts.

### Fixed

- **The app never applied the stored theme.** The header toggle wrote `caos.theme` at runtime but
  nothing read it back, so a reader who chose light got dark again on every reload and every deep
  link.
- **The Abrams law shipped as `f_c pprox rac{A}{B^{w/c}}`.** The literal was written
  without an `r` prefix, so `` became BEL, `` became formfeed and `	` became a tab; marking
  it raw afterwards froze the damage. Ruff was clean, tests passed, and KaTeX rendered the wreckage.
- Two expanded cases were unreachable in the app while the catalogue still counted them as
  published: the index fell back to lane `"unknown"`, which the navigator does not offer.
- Long expressions clipped silently in a half-width column; they now stack to full width and show
  their overflow.
- Tree nodes rendered raw LaTeX clipped inside their circles, so a variable read as `{amb`.
- Component terms printed their own LaTeX source instead of rendering as mathematics.
- uPlot read the generation axis as UNIX time and labelled it `12/31/69 9:00pm`; the log axis
  emitted a tick per minor step and smeared into an unreadable column.
- Every count went through the browser locale, so 2550 rows rendered as "2.550" and 12000
  evaluations as "12.000" for a Spanish-locale reader of the English page.
- The sidebar readout borrowed the chart-hover class, which is `display:flex`, putting its heading
  beside its numbers and cutting the last row.
- The subsample note reported "4000 of 4000 rows" because it read the array after replacing it.

### Added, after the first draft of these notes

- **A second search family.** Every rung of the ladder was genetic programming with one more
  mechanism attached, which is an excellent ablation OF genetic programming and a poor survey of
  symbolic regression. `search/sparse.py` adds the non-evolutionary family: a fixed library of
  nonlinear terms and sequentially thresholded least squares over a sweep of sparsity levels, the
  family behind FFX and SINDy. Written in numpy so the same module runs in the browser lane, and it
  runs on every case.

  It recovers the Lotka-Volterra right-hand side essentially exactly, because that law is a
  polynomial and therefore inside its span. On the saturating and exponential laws it reaches R2
  between 0.85 and 0.99 with structural distance near 1.0. A good fit and the wrong structure, from
  a method with no relationship to genetic programming at all.

- **The ingestion contract's warnings, in the app.** The pipeline detects that the flotation target
  takes 709 distinct values across 4000 rows and warns that fitting at that resolution may leak it.
  That warning was written to the audit manifest, which the app never opens, so the reader who most
  needed it was the only one who could not see it. It renders on the Context tab now, with the
  loader's applied defects beside it.

- **The measured ablation.** The Experiments page listed the question each rung answers and never
  showed a measured difference. It now reports, per rung, the cases that ran it, recoveries over
  the checkable configurations, the change against the rung above computed only over cases that ran
  both, median R2, median seconds and the cost multiple.

### Fixed, after the first draft of these notes

- **Every boolean in every artifact was an integer.** `bool` is a subclass of `int` in Python, so
  the JSON normaliser's integer branch swallowed them all and wrote 0 or 1 while the contract
  declared `boolean | null`. It survived because consumers tested truthiness; it broke the moment
  one compared identity, and the damage it had already done was `units_ok === false`, which is false
  when the value is 0, so the dimensional-consistency warning could never render.
- **A different search family was presented as one more rung of the ladder**, inside a dropdown
  labelled "Ladder rung" and a table whose premise is that each row adds one mechanism to the row
  above. The family is exported now, the selector groups by it, and no paired delta is computed
  across families.
- The case index counted "Ten cases carry a `truth_node`" in prose. It was 16 by then. Those counts
  are generated from the registry and gated.

### Fixed, after auditing every claim against the code that makes it

Four audits read the documentation, the docstrings and the site copy against the engine rather than
against each other. Everything below ran green before it was found, which is the point: none of it
was a crash.

**Six defects in the engine and the export, all of which changed what shipped.**

- **The ladder was not a ladder.** `r6-age-fitness-islands` omitted `multi_objective` while r5
  carried it and r7 turned it back on, so r6 added age and islands AND silently dropped complexity
  as an objective, falling from three-way NSGA-II survival to the two-way age-fitness one. The rung
  is labelled "age becomes an objective" and r4 is where the output is said to become a front. The
  Experiments page attributed the whole measured delta to islands.
- **Age-fitness inverted its own mechanism.** A child inherited `1 + min(parent ages)` and no age-0
  individual was ever injected. Genotypic age counts generations since the OLDEST ancestor, so the
  minimum lets an entrenched lineage reset its age by crossing with anything younger, which is the
  takeover the method exists to prevent, and with no injection the youngest age only climbs. Now
  `max`, plus one age-0 individual per island per generation, replacing a child so the population
  size and the evaluations per generation are unchanged.
- **The export could drop the member the artifact was about.** The front was capped at twelve and
  the selected index clamped with `min(index, len - 1)`, so where selection landed past the cap the
  published equation, tree and validation arrays described the last exported member while the score
  described the model selection actually chose. Ten variants across the corpus were in that state,
  one selecting index 18 of a front of 19.
- **The sparse arm measured complexity on something other than what it published**, a hand-rolled
  term tally rather than the node count the exporter writes. They disagreed on 25 of 39 artifacts,
  so the two families' fronts were not on the same axis.
- **`r8-unit-typed` could run entirely untyped without saying so**, either because the case declares
  no dimensions or because no expression over its inputs reaches the target dimension. The fallback
  carried a comment claiming it "marked the run"; nothing marked it. Recorded now as
  `unit_typed_status`, exported beside the request.
- **Three measurements were computed and discarded.** `tune_population` dropped the identifiability
  verdict that Levenberg-Marquardt computes per candidate, so a front whose constants are not
  jointly recoverable looked identical to one whose are. The tuning schedule and the lexicase
  down-sampling rate were absent from the artifact, against the engine's own docstring.

**The data itself.** Every `strogatz_*` file in the PMLB collection is headed `target, x, y`, with
the derivative FIRST, and the loader took the last column by the usual PMLB convention. The pipeline
was fitting `y` from `[dx/dt, x]`: predicting a state variable from the derivative, the inverse of
the question those cases claim to ask. Checked against the published right-hand side for `bacres1`,
the first column reproduces it to 4.9e-14 and the last column misses by 55.2. The Feynman files in
the same collection really do put the target last, so the convention was real, just not universal.

**Twelve megabytes of derivable data in every artifact.** The per-variant validation block carried
the residual against each input as `{x, residual}`, where `residual` was a byte-for-byte copy of
`y_true - y_pred` from the parity block beside it, repeated once per input, and `x` was a data
column repeated once per rung. On the flotation case that was 12.1 MB of a 12.6 MB file. The columns
now ship once per case and the browser subtracts.

**Claims that pointed at nothing.** Five of the seven generators declaring a `real_data_twin` named
a case id that exists in no registry and no source table. The Lotka-Volterra caveats promised that
the predator equation and the conserved quantity "ship as their own variants"; neither generator has
ever been written. `io/sources.py` recorded Feynman III.15.14 as a formula that is off by a relative
1.0 against the rows it ships with. `deploy/pages.md` described a workflow step that has never run.
`deploy/README.md` listed two files that have never existed. The App computed a "pending cases"
count by subtracting registry entries from expanded artifacts, giving -13.

**A venv nobody had.** `setup.{sh,ps1}` created `.venv-pipeline` for a "heavy offline lane" and
`.venv` for a "runtime/live-thin lane". Only `.venv` was ever created, so every guide telling a
reader to run `.venv-pipeline/bin/python` gave an instruction that could not work, and
`smoke.{sh,ps1}` pointed at that missing interpreter too. There is no heavy lane, because the engine
is hand-written numpy so the same modules run in the browser, and no thin runtime lane to install,
because the live lane runs in the reader's browser through Pyodide.

**Eight dead modules**, each with a docstring asserting a role it did not have, including
`core/rng.py` ("the single RNG factory ... always thread one made here", threaded by nothing) and
`core/gate.py`, whose classifier declared that its verdict "goes into the manifest, and CI fails on
mislabeling" while having zero callers, `build_manifest` hardcoding `"lane": "precompute"`, and the
CI check comparing a key that was never written. The gate is rewritten around what actually decides
the lane here (whether the browser can regenerate the case's data) and wired; the rest are gone,
along with four tracked empty directories shadowing the real package layout.

**The harnesses were not in the repository they verify.** The CHANGELOG listed
`tools/visual-verify/symlab-workbench.mjs` under guards, beside `tests/*.py` paths that really are
here; it was not, nor were the two other visual harnesses nor the live-parity harness. Every claim
of the form "this is checked rather than asserted" pointed at something a reader could not run. All
four are in `tools/` now, with a README saying what each asserts.

**The App, screenshot-verified rather than inferred.** The sidebar readout is the last block of a
scrolling column, so at 1600x1000 it rendered "RUNGS" and "BEST R2" as headings with their values
cut off, which reads as missing data. It sticks to the bottom of its own scroll container now.

### Guards added

Each of these exists because the corresponding defect survived a green build:

- `tests/test_generator_truths.py` and `tests/test_physics_truths.py`: every truth reproduces its
  own data, every absence carries a written reason of more than 25 words, and every tolerance
  carries a justification so "the identity is approximate" cannot be confused with "we widened the
  tolerance until it passed".
- `tests/test_no_control_characters.py`: no control byte in the package source.
- `tests/test_manifests_match_reality.py`: every pin installed at its pinned version, every pinned
  runtime package actually imported, every third-party import pinned somewhere.
- `tests/test_case_docs_match_code.py`: no case page may contradict the code it documents, and the
  generated counts must match the registry.
- `tests/test_export_types.py`: the payload must carry the TYPES the contract declares, checked on
  the normaliser and end to end on a real artifact.
- `tests/test_contract_conformance.py`: the payload and the declared interfaces must match in BOTH
  directions. TypeScript only checks the consumer; a field the producer stops writing, or writes
  without declaring, compiles perfectly.
- `tests/test_sparse_search.py`: evaluating the published expression must reproduce the reported
  loss, the arm must be deterministic, and a law inside the library's span must be recovered.
- `tools/visual-verify/workbench.mjs`: six tabs across both themes and both languages, asserting
  the provenance labels, populated dropdowns, no overflow, no console error, no untranslated
  interface copy, and that every class the app renders has a CSS rule behind it. It, the two other
  visual harnesses and the live-parity harness were written against this product but lived outside
  the repository, so every claim of the form "this is checked rather than asserted" pointed at
  something a reader could not run. They are in `tools/` now, with `tools/README.md` describing
  what each one asserts and how to run it.

## 0.03.000 - 2026-07-22

### Added

- The `docs/` wiki in the house tree: a folder per theme with a same-named landing page and numbered
  deep pages. Covers the architecture, every method family with the mathematics this build uses, the
  case taxonomy, the guides, and both data contracts.
- Seven hand-authored inline SVG figures across Methodology, Implementation and Experiments. Inline
  rather than image files, because an inline element inherits the page CSS variables and one
  declaration then serves both themes.
- Display names, category names and the ground-truth flag in the case index, so the interface never
  has to render an internal single-letter code.
- `scripts/rebuild_index.py`, which rebuilds the index from whatever is already baked without
  re-running any search.

### Changed

- The App page now uses the shared shell `CaseSelector` instead of a hand-rolled sidebar list. The
  page is the house two-zone workbench: a control sidebar carrying the data-source lane, the case
  selector grouped by category, the search-configuration ladder, the view controls and the live
  readout; and a main area carrying only the tabs and their views.
- The measurement labels now name what they measure. "accuracy rate" was a COUNT of configurations
  clearing the 0.999 threshold and was read as a statement about model accuracy; it now reads
  "above R2 > 0.999" as a count, with the best held-out R2 shown alongside it.

### Fixed

- The live lane never ran. It called `importScripts` inside a module worker, which throws, and the
  engine source was never copied into the served tree, so every module fetch would have 404ed even
  after that. Now a dynamic ESM import of the Pyodide build, with `copy-data.mjs` copying the 17
  browser-safe package modules into `public/engine/` and failing the build if one is missing.
  Verified by driving a real browser against the deployed site.
- A relative vite base rendered every route blank on the live site behind a green build AND a
  successful deploy: the resulting `BASE_URL` cannot serve as a React Router basename. Base is now
  absolute and the reason is recorded in the config.
- The sidebar quoted the registry total directly above a much shorter list of published cases.
- Five CSS classes were written into the JSX and never styled, which is how the case strip shipped
  rendering as run-together text.
- A duplicate key in the loader registry, caught by ruff, where the second entry silently shadowed
  the first.

## 0.02.000 - 2026-07-22

### Added

- The full six-page bilingual application with the in-app architecture modal and its five theme-aware
  SVGs, deployed to `symlab.fasl-work.com`.
- The real data layer: a source registry with SHA-256 pinning and provenance sidecars, loaders that
  assert schema before accepting a file, and a fetcher that rejects storage-pointer downloads.
- 25 cases across six categories, the six named pipeline stages, and the triple-equivalence
  evaluator that publishes the failure rate of its own symbolic test.

### Fixed

- A units defect on the reciprocal operator, where the `sub` rule shared by the binary quotient and
  the unary reciprocal indexed a second child that does not exist. Found by running the pump-affinity
  case; fixed with regression tests.
- Complexity was reported from the pre-scaling expression, understating one of the two axes the whole
  product is read on.
- The textbook nested-loop non-domination sort dominated wall-clock at 39.2 s against 0.8 s for the
  same budget. Vectorised; identical result.

## 0.01.000 - 2026-07-21

### Added

- The product base instantiated from the CAOS archetype, and the shared expression core: nodes,
  operators, vectorised evaluation, the shared node id space, dimensional analysis constraining
  generation, interval guards with no protected operators, closed-form linear scaling, three
  complexity measures with description-length selection, and addressable LaTeX rendering.
- The search layer with every classical rung as a switch defaulting off, and a bounded exhaustive
  search issuing a completeness certificate with its caveats attached.
- 18 first-principles generators transcribed from named sources, each with its governing equation,
  parameter ranges, validity window and caveats.
- CONTRACT 2 frozen at `schema_version 1.0.0`, written before any user interface existed.

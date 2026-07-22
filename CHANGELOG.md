# Changelog

All notable changes are documented here. Format follows Keep a Changelog; newest on top.
Version format is X.XX.XXX; the manifest carries the semver form with zeros dropped.

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

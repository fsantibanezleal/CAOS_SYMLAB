# Read the workbench

The App page is one case at a time. This guide says what each control does and, more importantly, what each
panel is claiming, because the single most common misreading of a symbolic regression tool is treating the
equation on screen as the law that was supplied rather than the result that was found.

## The two zones

Everything you choose lives in the **left sidebar**. Everything the lab reports lives in the **tabs on the
right**. No selector sits in the content area, and the content area never gives up width to a list.

### Sidebar, top to bottom

| Control | What it does |
|---|---|
| Data source | Generator, or measured data. A generator has a published law behind it, so recovery is checkable. Measured data does not, and there are no knobs to turn: only what was recorded. |
| Category | Narrows the case list. The category codes in the registry are internal; the dropdown shows their human names with a count. |
| Case | The case itself. The selection is mirrored into `?case=`, so a case can be shared as a URL. |
| Method | The search configuration, grouped by family. Within the genetic-programming ladder each rung adds exactly ONE mechanism to the one above it, so a measured difference is attributable to that named change rather than to several at once. The sparse-regression arm sits in a second group because it is a different family, not a further rung: compare it against the ladder as a whole. |
| View | Long form wraps a many-term sum across lines, because KaTeX cannot break display maths on its own. Raw output shows what the engine produced before prettifying. Collapse-below-influence hides low-influence subtrees so a large expression stays readable. |
| Readout | Row accounting, rung count, best held-out R2, and the two counts below. |

The two counts in the readout are counts of **configurations**, not statements of accuracy:

- **above R2 > 0.999** is how many rungs cleared the accuracy threshold.
- **structure recovered** is how many returned an expression equivalent to the published law, or "not checkable"
  when no such law exists.

The gap between those two numbers is the measurement this lab exists to make. Fitting well is not the same as
having found the law.

## Tab 1, Expression

The panel is a comparison, not a display.

- **FOUND BY THE SEARCH** is the result. The search received the data columns and nothing else. The
  configuration that produced it is named beneath the label, and its held-out R2, complexity and description
  length sit under the mathematics.
- **THE RELATIONSHIP WE EXPECTED** is the published law, shown only where one exists, and used ONLY for scoring.
  The search never sees it. Where no law exists, that side says so and states that the expression on the left is
  a finding with no reference: it contributes to the error metrics and to no recovery rate.
- Between them is the **verdict**: recovered, not recovered, or the scorer could not decide. The symbolic and
  numerical tests are reported separately, and a disagreement between them is shown rather than hidden.

Two more things on this tab are results rather than presentation:

- **Constant rounding.** Constants are rounded for readability only when the measured relative error stays
  inside tolerance. When it does not, the rounding is REFUSED and full precision is shown, with a note saying so.
  Prettier output that is quietly a different model is not an improvement.
- **Dimensional consistency.** Where an expression is dimensionally inconsistent, the reason is stated.

## Tab 2, Structure

The tree and the components, both keyed by the same integer node ids the equation uses, so hovering a term, a
node or a row highlights the same subexpression in all three.

Node radius encodes **influence**: the drop in R-squared when that subtree is replaced by its mean. It is
computed once in the pipeline, so the tree, the equation highlighting and the contribution table cannot disagree
about which part of the expression matters.

The components table answers what the tree cannot: which additive term actually carries the signal. A term can
be structurally large and contribute almost nothing, and that is the most common way a discovered expression is
worse than it looks. The variables panel states how many of the available inputs the expression ignores, which
is either correct variable selection or a search that never reached them.

## Tab 3, Parity and residuals

Parity first, because it is the view anyone can check by eye, with test points highlighted: those are the rows
the search never saw.

**Residuals against each input** second, because that is where a missing term shows and a parity plot hides it.
A flat, structureless band means the expression captured what that variable does. A curve, a fan or a step means
it did not, and that is a concrete finding rather than a global error number.

**Outside the training support** third. The shaded band is the range the search was fitted over; outside it
nothing constrained the expression, and that is where the benchmark literature says every method degrades. Grid
points where the expression is undefined are counted and stated rather than dropped to make the curve look
continuous.

**Partial dependence** last, as a summary of shape rather than of error.

## Tab 4, Live (your browser)

The same Python engine, running in your browser through Pyodide, at a reduced budget. It is not a different
implementation: the browser loads the same engine modules the offline pipeline runs, staged into
`public/engine/` at build time. Nothing starts until you press run.

Read it as a demonstration of the ENGINE, not as a check on this case's numbers. The rung is fixed at
`r4-multi-objective`, the data is regenerated in the browser at 240 rows, and the population and generation
budget are whatever you set, so expect a simpler expression than the Expression tab shows. On a case with no
generator behind it (the measured datasets and the published-physics suites, 9 of the 25 registry cases) the
worker currently falls back to the Monod generator instead of refusing, so what runs there is not the case on
screen. That fallback is a known defect in `frontend/src/live/search.worker.ts`.

## Tab 5, Front and search

The accuracy-versus-complexity **Pareto front** is the deliverable, not a summary of one. Every point is an
expression; clicking one loads it into every other tab.

The ring marks the point chosen by **minimum description length**, not by best accuracy. Choosing by accuracy is
exactly how a method exceeds 0.999 while recovering the wrong structure, so the default marker is the honest one.

Below it, the convergence and diversity curves and the measured cost of the rung: seconds, evaluations,
duplicates avoided and candidates rejected by the interval guard. The cost is shown because the benchmark
literature names budget unfairness as a standing problem, and comparing rungs at equal generation count is not
a fair comparison when they do not cost the same. Across the committed manifests, taking each case's Koza
baseline as 1, the median wall-clock ratios are about 1.3 for linear scaling, 1.7 for constant tuning, 24 for
age-fitness islands, 30 for epsilon-lexicase and 150 for deduplication, while the sparse-regression arm comes
back in about a hundredth of the baseline.

## Tab 6, Context

Provenance, sampling ranges, the recorded defects, the split note and, where the case supports it, the bounded
exhaustive **certificate** with its caveats. A certificate whose enumeration was truncated says so: the
completeness claim does not hold in that case.

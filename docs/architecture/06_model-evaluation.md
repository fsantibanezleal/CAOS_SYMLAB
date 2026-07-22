# Model evaluation (the TEST stage)

`stages/evaluate.py` reports held-out metrics from a disjoint draw, never the training set. In SymLab it does
something a conventional regression pipeline does not have to do: it scores **two different claims** and refuses
to merge them.

## The two claims

**Accuracy** is whether the returned expression predicts held-out rows well. It is reported for every case,
against every rung of the ladder, as R2 and mean squared error on the test split, plus a separate mean squared
error on the extrapolation split where one exists. A configuration counts as an accuracy solution at
`ACCURACY_R2_THRESHOLD = 0.999` on the test split.

**Recovery** is whether the returned expression IS the published law. It is reported only where such a law
exists. A plant or instrument dataset has no closed form to recover, so its recovery is `null`, and the app says
"not checkable" rather than printing a zero. Reporting an unmeasurable quantity as zero would be a false
statement about the method.

The gap between the two is the headline measurement of this lab. A method can clear R2 > 0.999 on held-out rows
while returning a structure that has nothing in common with the law that generated them.

## How equivalence is decided

Three tests, run against a truth expression the search never sees:

| Test | How | What it misses |
|---|---|---|
| symbolic | simplify the difference through sympy and ask whether it is zero | can time out, or fail to simplify a form that is in fact equivalent |
| numerical | evaluate both over a probe box drawn from the training support and compare relative error | agrees with a wrong expression that happens to match inside the sampled box |
| structural | a normalised edit distance in [0, 1] over the two canonical pre-order label sequences | reports a distance, never a yes or no |

The verdict itself (`EquivalenceVerdict.recovered`) is the symbolic answer where sympy decided, and the
numerical answer otherwise. The structural distance is reported alongside and never decides. It is computed by
`sreval[symbolic]==0.1.0` (MIT), the evaluation harness extracted from this lab as its own package because
telling "the method failed" apart from "the scorer failed" is a general need; the local loop in
`stages/evaluate.py` is the browser-lane fallback for Pyodide, where sreval is never installed, and
`tests/test_sreval_agrees.py` asserts the two return identical numbers. The dependency is called rather than
merely imported: an earlier version pinned it, documented it as "used here", and never referenced it.

The symbolic and numerical tests usually agree inside the sampled box and differ outside it, which is exactly
where a wrong expression gives itself away, so a **disagreement is published rather than resolved silently**. A
symbolic test that could not decide is recorded as a property of the SCORER, not of the method: the artifact
carries `symbolic_test_failure_rate` so a reader can tell "the method failed" apart from "the scorer failed".

## What the truth is, and what it is not

The truth is used only for scoring. It is resolved in `stages/preprocess.py`, carried on `PreparedCase`, and
handed to the evaluator and to the export. It is never passed to the search, and the artifact records both the
expression that was found and the law it was scored against, so a reader can compare them directly rather than
taking the verdict on faith.

Each truth also carries a **regime**, because two different difficulty claims otherwise hide under one word:

- `structure`: the physical parameters were supplied as input columns, so only the FORM was unknown. This is the
  convention the published physics benchmarks use.
- `structure+constants`: the numbers are baked into the generator and had to be recovered as well.

## Selection

The member reported as the answer is chosen by **minimum description length** in nats, not by best accuracy.
Selecting by accuracy is the mechanism by which a method scores above the threshold while recovering the wrong
structure, so the honest default is the criterion that pays for structure and for constants as well as for
residuals.

Metrics are written into each case manifest and surfaced on the Experiments and Benchmark views. Nothing on
those pages is computed in the browser: every number is replayed from a committed artifact produced by a seeded
offline run.

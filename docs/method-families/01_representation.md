# 1. Representation, and why there are no protected operators

An expression is an immutable tree. Nodes carry no identity of their own; identity is assigned by a
pre-order walk, so the integer id space is IDENTICAL in the LaTeX annotations, the flat node list
shipped to the web, and the per-term references. That shared space is not a convenience: it is what
lets hovering a term in the equation highlight the same subtree in the tree, with no second parallel
mapping to keep synchronised.

## The decision that separates this from a tutorial implementation

The classical habit defines a PROTECTED division returning 1.0 when the denominator is zero. That
silently changes the function being searched. The search never learns to avoid the singularity, and
the resulting expression is only meaningful on the sample it was fitted to. The moment you
extrapolate, the protection is gone and the model diverges.

There are no protected operators here. Interval arithmetic propagates the input ranges through the
candidate and REJECTS anything undefined anywhere in the box, before a single evaluation.

    admissible(f)  iff  for all x in B:  f(x) is finite  and  |f(x)| <= M

`B` is the input box, widened beyond the training range so the guard means "safe where we intend to
extrapolate" rather than "safe on this sample". `M` is a magnitude bound discarding expressions that
are defined but numerically useless.

## What the guard rejects, concretely

| Expression | Box | Verdict |
|---|---|---|
| `1/x` | x in [-1, 1] | rejected: the denominator interval contains zero |
| `1/x` | x in [2, 5] | admissible: the pole is outside the box |
| `log(x)` | x in [0, 5] | rejected: the argument reaches zero |
| `exp(x)` | x in [0, 1000] | rejected: overflows float64 above about 709 |
| `sqrt(x)` | x in [-1, 4] | rejected: the argument goes negative |

## What it costs, and why the cost is reported

Rejecting rather than protecting discards candidates a protected engine would have kept. That
rejected fraction is counted and reported on every variant, because it says something real about the
primitive set and the data. An engine rejecting most of its population on a given case is telling
you the primitives do not suit the problem, which is information, not noise.

## Operators and named primitive sets

Fourteen operators are available. A run records WHICH set it was allowed, because two engines given
different primitive sets were not solving the same problem, and comparing their numbers without
saying so is one of the standing failures in the benchmark literature.

| Set | Operators |
|---|---|
| `arithmetic` | add, sub, mul, div |
| `koza` | arithmetic plus sin, cos, exp, log |
| `physics` | koza plus square, sqrt, inv |
| `rational` | add, sub, mul, div, square, inv |
| `full` | all fourteen |

## Reference

Keijzer, M. (2003). Improving symbolic regression with interval arithmetic and linear scaling.
EuroGP 2003, Lecture Notes in Computer Science 2610, pages 70 to 82,
doi:10.1007/3-540-36599-0_7.

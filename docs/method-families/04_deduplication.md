# 7. Deduplication

Two kinds of duplicate waste a search budget, and they are caught differently.

**Structural duplicates** are syntactically identical up to the argument order of commutative
operators. `a + b` and `b + a` are the same expression written twice. A canonical key that sorts the
arguments of commutative operators catches these before any evaluation happens, which is why it is
the cheap check and runs first.

**Semantic duplicates** are structurally different and produce identical output. Detecting them
requires an evaluation, so the check runs second and on a SUBSAMPLE of the rows, `min(64, n_rows)`:
semantic identity is a screening test, not a proof, and evaluating every rejected candidate on every
row was measurably expensive for no additional information. The key is a blake2b digest of the
output vector rounded to 8 decimals, chosen over the builtin `hash` because that one is randomised
per process, which would make the measured effect of this rung a property of interpreter startup.

## The measured fraction is the point

The count of duplicates avoided is reported on every variant. It is a measurement about the search,
not an implementation detail: a run avoiding tens of thousands of duplicate evaluations is telling
you the population has converged and the budget is being spent re-deriving what it already has.

## A defect worth recording

The first implementation retried indefinitely when a child collided with something already seen. Once
a population converges almost every child collides, so the loop burned whole generations rejecting
duplicates. It is now bounded by a retry budget of eight attempts per population member, with a
top-up from the best of the current generation so the population never silently shrinks mid-run: a
shrinking population would change the search budget partway through and make the ablation dishonest.

An earlier version of the comment on that fix blamed deduplication for the entire slowdown of the
combined rung. Isolating the switches showed otherwise:

| Configuration | Wall clock |
|---|---|
| baseline | 0.30 s |
| plus deduplication | 0.75 s |
| plus epsilon-lexicase | 6.73 s |
| plus both | 13.43 s |

Deduplication costs about 2.5 times; epsilon-lexicase costs about 22 times. The wrong attribution is
recorded here because a misattributed cost in a comment misleads exactly as much as a wrong number in
a published result.

The conditions behind that table (population 100, 10 generations, 120 rows, seed 7) do not name the
case or the primitive set, so the seconds are not reproducible from this page. Re-run at the same
budget on 120 synthetic rows over three inputs, the ordering holds and the multipliers move:
0.19 s baseline, 0.38 s adding deduplication, 1.43 s adding epsilon-lexicase, 7.61 s adding both,
with 335 duplicates avoided by the deduplication rung alone and 577 by the combined one. The
conclusion the table exists to support, that the dominant cost is selection and not deduplication,
survives; the multipliers are a property of the case.

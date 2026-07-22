# 12. Bounded exhaustive search: the only rung that can prove a negative

Every other method returns the best expression it FOUND. Bounded enumeration returns the best that
EXISTS, up to a given complexity over a given primitive set. That difference justifies the cost, and
it makes this the best interactive demonstration in the product: the space is finite and can be
watched shrinking as the constraints tighten.

## What the certificate claims

> Over the primitive set P and the variables V, every structurally distinct expression of at most k
> nodes was enumerated and fitted. No expression in that space achieves a lower description length
> than the one reported.

## What it does NOT claim

- That no simpler law exists. A law requiring an operator outside P is unreachable, and its absence
  here is not evidence of anything.
- Anything at all about expressions of k+1 nodes.
- That the reported expression is the true generating process. Fitting is not discovering, which is
  why this lab reports description length rather than accuracy alone.
- Exhaustive coverage of constants. Constants are fitted numerically AFTER enumeration, so only
  expression STRUCTURES are exhaustively covered.
- Any published codelength. The description length used is the one this build defines and states.

If the enumeration hits its cap of 200 000 distinct expressions, the certificate comes back with
`complete = False` and an extra caveat saying in words that the completeness claim does not hold for
that run and must not be presented as a certificate. A truncated enumeration proves nothing and must
never be presented as if it did.

## How the enumeration stays finite

Built bottom up by node count, with deduplication by canonical key so commutative rearrangements are
enumerated once. Without that the count explodes by a factor growing with the number of commutative
operators in the set. Constants enter as a single placeholder leaf and are fitted afterwards.

## Measured in this build

573 expressions enumerated over four operators up to 5 nodes, 546 admissible after the interval
guard, recovering `x0 * x1` exactly at zero mean squared error, with the certificate complete.

The conditions, so the count can be reproduced rather than trusted: the `arithmetic` primitive set
(add, sub, mul, div), TWO input variables plus the constant placeholder, `max_nodes = 5`, and the
interval guard on with a margin of 0.25. Re-running that returns exactly 573 enumerated, 546
admissible, 370 of them carrying a constant to fit, `complete = True`, and `(x0 * x1)` at a loss of
0.0. The count is a function of the variable count as much as of the operator set: three variables
is a different number and the two are not comparable.

The pipeline's own certificate stage runs the same enumeration at `max_nodes = 7` over that
primitive set.

## Reference

Bartlett, D. J., Desmond, H. and Ferreira, P. G. (2023). Exhaustive Symbolic Regression. IEEE
Transactions on Evolutionary Computation, doi:10.1109/TEVC.2023.3280250.

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

If the enumeration hits its cap, the certificate is marked INVALID and says so explicitly. A
truncated enumeration proves nothing and must never be presented as if it did.

## How the enumeration stays finite

Built bottom up by node count, with deduplication by canonical key so commutative rearrangements are
enumerated once. Without that the count explodes by a factor growing with the number of commutative
operators in the set. Constants enter as a single placeholder leaf and are fitted afterwards.

## Measured in this build

573 expressions enumerated over four operators up to 5 nodes, 546 admissible after the interval
guard, recovering `x0 * x1` exactly at zero mean squared error, with the certificate complete.

## Reference

Bartlett, D. J., Desmond, H. and Ferreira, P. G. (2023). Exhaustive Symbolic Regression. IEEE
Transactions on Evolutionary Computation, doi:10.1109/TEVC.2023.3280250.

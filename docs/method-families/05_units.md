# 8. Units as a constraint on generation

Every quantity carries a seven-vector of exponents over the SI base dimensions, in the fixed order
length, mass, time, electric current, temperature, amount, luminous intensity. A dimensionless
quantity is the zero vector.

There are two uses and they differ in kind.

**Checking** a finished expression is a filter, and it is the weaker use: the evaluation has already
been spent by the time the check runs.

**Constraining generation** is the strong use. The generator refuses to build a node whose units
cannot work, so the search never spends an evaluation on the sine of a length, or on adding a mass to
a time. Filtering wastes the evaluation; constraining never makes it.

## The rules

    dim(a * b)  = dim(a) + dim(b)
    dim(a / b)  = dim(a) - dim(b)
    dim(sin a)  requires dim(a) = 0, and yields 0
    dim(a^2)    = 2 * dim(a)
    dim(sqrt a) = dim(a) / 2, and is REFUSED when any exponent is odd

That last refusal matters. The square root of a length has no representation in an integer exponent
lattice, so the generator declines to build it rather than rounding an exponent and producing a
quantity that does not exist.

## A defect this found

The `sub` unit rule is shared by the binary quotient and the UNARY reciprocal. The first
implementation indexed the second child unconditionally and raised an IndexError on `inv`, which
surfaced on the pump-affinity case where reciprocals are exactly what the physics calls for. A
reciprocal negates the exponents. Fixed, with regression tests for the reciprocal rule and for the
reciprocal of a frequency being a time.

## Necessary, never sufficient

Unit consistency is a necessary condition for a physical law and never a sufficient one. A
dimensionally perfect expression can still be the wrong law, which is precisely why this lab has an
evaluation protocol at all: a plausible-looking fit is not a discovery.

## When the rung is omitted

A case whose inputs carry no declared physical dimensions omits this rung from its variant list
entirely, rather than showing a control that silently does nothing. That omission is real: the train
stage skips any variant whose config sets `unit_typed` when the case declares no units, and the
feature stage writes the reason into the case payload.

The other failure mode is NOT handled that way today, and the page says so rather than describing an
intention. When the declared inputs cannot reach the target dimension, `typed_population` returns an
empty list, and the engine falls back to unconstrained `ramped_half_and_half` initialisation and
carries on. Nothing in the result, the counters or the exported config records that the fallback
happened, so a run labelled "unit-typed" can be an unconstrained run. `grow_typed`'s own docstring
says the caller reports it instead of falling back; the caller does the opposite. Until that is
fixed, treat a unit-typed chip on a case whose inputs cannot span the target as unverified.

## References

- Buckingham, E. (1914). On physically similar systems; illustrations of the use of dimensional
  equations. Physical Review 4(4), pages 345 to 376, doi:10.1103/PhysRev.4.345.
- Tenachi, W., Ibata, R. and Diakogiannis, F. I. (2023). Deep symbolic regression for physics guided
  by units constraints. The Astrophysical Journal 959(2), 99, doi:10.3847/1538-4357/ad014c.

# 07. Sparse regression over a fixed basis, the non-evolutionary arm

Every other page in this folder describes a mechanism inside a genetic-programming search. This one
describes a search that does no evolution at all, and it is here because a ladder made only of GP
rungs is an excellent ablation of GP and a poor survey of symbolic regression.

Implemented in [`search/sparse.py`](../../data-pipeline/symlab/search/sparse.py) and run as the
`sparse-regression` arm on every case.

## The method

Build a library of candidate terms once, then choose a sparse subset of them by least squares.

$$ y \approx \sum_{k \in S} c_k\, \phi_k(x) $$

where $\{\phi_k\}$ is the library and $S$ is the selected support. The library used here is
deliberately modest: the constant, and for each input $x_j$ the terms $x_j$, $x_j^2$, $1/x_j$,
$\sqrt{x_j}$, $\log x_j$ and $e^{x_j}$, plus every pairwise product $x_a x_b$.

Selection is **sequentially thresholded least squares** (STLSQ): fit the full library, delete every
coefficient below a threshold, refit on what survives, repeat until the support stops changing.
Sweeping the threshold sweeps the accuracy-versus-complexity front.

This is the family behind FFX (McConaghy, 2011) and, for dynamical systems, SINDy (Brunton, Proctor
and Kutz, 2016). Neither library is vendored here, for the same reason the GP engine is
hand-written: the live lane runs these modules in the browser through Pyodide, so anything that
cannot be written in numpy cannot ship.

## What it buys

**It is deterministic.** No seed, no population, no run-to-run variance. Where it recovers a law it
recovers it every time, and where it fails it fails identically. That makes it a harder baseline to
dismiss than a lucky evolutionary run, and the test suite asserts it: the same data gives the same
front regardless of the seed passed in.

**The front comes out by construction** rather than being searched for. One model per sparsity
level, already ordered.

**It is nearly free.** On a 400-row case it returns in single-digit milliseconds, against tens of
seconds for the GP rungs. Any claim that a GP rung "found" something has to beat this first.

## What it cannot do, stated plainly

The library is fixed before the data is seen, so the method can only ever return a linear
combination of terms somebody chose in advance. **Nested structure is unreachable.** A saturation
inside a product, or an exponential of a reciprocal, is not in the span at any sparsity level and no
amount of budget will find it.

That is not a defect to be apologised for; it is the measurement. Genetic programming exists to
search the space of compositions, and running both families over the same cases is how a reader sees
the size of the gap between "a good linear combination of known shapes" and "the law".

On the first-principles generators the arm recovers the Lotka-Volterra right-hand side essentially
exactly, because that law IS a polynomial and therefore is in the span. On the saturating and
exponential laws it reaches R2 in the 0.85 to 0.99 range while the structural distance to the true
law stays near 1.0: a good fit, the wrong structure, which is the phenomenon this entire lab is
built to report.

## Two ways it failed silently, and what stops them now

Both produced a running, green, plausible-looking search that was wrong, and neither raised
anything. Both are pinned by tests.

**Unnormalised thresholding.** The library mixes $x$, $x^2$, $\log x$ and $e^{x}$, whose columns
differ by many orders of magnitude. The least-squares coefficients then land around $10^{-25}$ on
the enormous columns, and a single threshold applied to those numbers is meaningless: the first
implementation deleted every coefficient at every threshold and returned the mean of $y$ for every
case, with no error and no warning. Thresholding is a statement about how much a term CONTRIBUTES,
so the columns are scaled before the comparison and the coefficients scaled back afterwards, and
the sweep is expressed as a fraction of the target scale so one set of numbers works on a target in
megawatts and on a target that is a fraction.

**A column that was not its own expression.** The library column was originally computed by a numpy
lambda that clipped $e^{x}$ to avoid overflow and took $\log|x|$, while the expression the method
published did neither. The fit was performed against one function and reported as another, and the
R2 measured on the returned expression came out at minus infinity. There is now one definition: the
column is produced by evaluating the expression, and any term that is not finite everywhere is
DROPPED rather than zero-filled, because a zero-filled column still enters the fit, still gets a
coefficient, and still ships inside the published formula.

The reported loss is likewise measured by evaluating the published expression, not by the matrix
product that produced the coefficients. The two agree to about $10^{-6}$, because a tree evaluation
and a matrix product sum in different orders, and the number that ships has to be the one a reader
reproduces from the formula on screen.

## References

- McConaghy, T. (2011). FFX: Fast, Scalable, Deterministic Symbolic Regression Technology. In
  *Genetic Programming Theory and Practice IX*, 235-260. DOI 10.1007/978-1-4614-1770-5_13
- Brunton, S. L., Proctor, J. L., and Kutz, J. N. (2016). Discovering governing equations from data
  by sparse identification of nonlinear dynamical systems. *PNAS* 113(15), 3932-3937.
  DOI 10.1073/pnas.1517384113

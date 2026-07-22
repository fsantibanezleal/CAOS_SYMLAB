"""Constant tuning: stop asking evolution to discover numbers it can solve for.

A tree genetic-programming search spends a surprising share of its budget nudging numeric leaves
towards values that a local optimiser reaches in a handful of iterations. Two rungs of the ladder
address that, and they are complementary rather than alternatives:

- **Linear scaling** (in `model/scaling.py`) solves the outermost multiplicative and additive
  constants in closed form, for free, for every candidate.
- **Nonlinear least squares**, here, solves ALL the numeric leaves jointly by Levenberg-Marquardt,
  then writes the fitted values back into the tree. Writing them back is what makes it Lamarckian:
  the improvement is inherited, not rediscovered each generation.

The cost is real and is the reason this is a separate rung with its own ablation: tuning every
candidate every generation is far more expensive than tuning the survivors occasionally. The engine
therefore applies it on a schedule, and the manifest records that schedule, because two runs with
different tuning budgets are not comparable.

One honest failure mode is handled explicitly. When two constants in an expression are redundant,
for example the `a` and `b` in `a * (b * x)`, the fit is degenerate: infinitely many pairs give the
same output, the Jacobian is rank-deficient, and the optimiser can wander. `collapse_redundant`
detects the rank deficiency and reports it, so a candidate whose parameters are not identifiable is
labelled rather than silently reported with arbitrary values.

Reference transcribed from the persisted research: Kommenda, M., Burlacu, B., Kronberger, G. and
Affenzeller, M. (2020). Parameter identification for symbolic regression using nonlinear least
squares. Genetic Programming and Evolvable Machines 21:471-501, doi:10.1007/s10710-019-09371-3.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..model.expr import Node, constants, evaluate, is_valid, n_constants, set_constants


@dataclass(frozen=True)
class TuneResult:
    """What tuning achieved, and whether the result is trustworthy."""

    expression: Node
    loss_before: float
    loss_after: float
    iterations: int
    improved: bool
    identifiable: bool
    note: str = ""


def _mse(y: np.ndarray, prediction: np.ndarray) -> float:
    if not is_valid(prediction):
        return float("inf")
    return float(np.mean((y - prediction) ** 2))


def _jacobian(expression: Node, theta: np.ndarray, X: np.ndarray, *, step: float = 1e-6) -> np.ndarray:
    """Forward-difference Jacobian of the prediction with respect to the constants.

    A finite-difference Jacobian is used rather than an analytic one because the operator table is
    open: a product would have to supply a derivative for every primitive, including any a case adds.
    The step is scaled by the magnitude of each parameter so it stays meaningful across the range of
    values constants actually take.
    """
    base = evaluate(set_constants(expression, theta), X)
    jacobian = np.zeros((X.shape[0], len(theta)))
    for j in range(len(theta)):
        h = step * max(1.0, abs(float(theta[j])))
        perturbed = theta.copy()
        perturbed[j] += h
        shifted = evaluate(set_constants(expression, perturbed), X)
        if not is_valid(shifted):
            jacobian[:, j] = 0.0
            continue
        jacobian[:, j] = (shifted - base) / h
    return jacobian


def collapse_redundant(jacobian: np.ndarray, *, tolerance: float = 1e-8) -> tuple[bool, int]:
    """Detect a rank-deficient Jacobian, meaning the constants are not jointly identifiable.

    Returns `(identifiable, rank)`. A rank below the parameter count means at least one constant is
    redundant given the others, so its fitted value carries no information and must not be reported
    as if it did.
    """
    if jacobian.size == 0:
        return True, 0
    singular_values = np.linalg.svd(jacobian, compute_uv=False)
    if singular_values.size == 0:
        return True, 0
    largest = float(singular_values[0])
    if largest <= 0:
        return False, 0
    rank = int(np.sum(singular_values > tolerance * largest))
    return rank >= jacobian.shape[1], rank


def levenberg_marquardt(
    expression: Node,
    X: np.ndarray,
    y: np.ndarray,
    *,
    max_iterations: int = 25,
    damping: float = 1e-3,
    tolerance: float = 1e-10,
) -> TuneResult:
    """Fit the numeric leaves by Levenberg-Marquardt and write the result back into the tree.

    Implemented directly rather than delegated, so the live browser lane can run it too: the
    offline lane could call out to a solver, but then the two lanes would be running different
    algorithms and the parity test between them would be meaningless.
    """
    theta = np.array(constants(expression), dtype=np.float64)
    if theta.size == 0:
        prediction = evaluate(expression, X)
        loss = _mse(y, prediction)
        return TuneResult(expression, loss, loss, 0, False, True, "no constants to fit")

    current = theta.copy()
    prediction = evaluate(set_constants(expression, current), X)
    if not is_valid(prediction):
        return TuneResult(expression, float("inf"), float("inf"), 0, False, True, "invalid at start")
    loss_before = _mse(y, prediction)
    best_loss = loss_before
    lam = damping
    iterations = 0
    identifiable = True
    rank_note = ""

    for iterations in range(1, max_iterations + 1):
        residual = y - evaluate(set_constants(expression, current), X)
        jacobian = _jacobian(expression, current, X)
        if iterations == 1:
            identifiable, rank = collapse_redundant(jacobian)
            if not identifiable:
                rank_note = f"parameters not identifiable: rank {rank} of {len(current)}"

        jtj = jacobian.T @ jacobian
        jtr = jacobian.T @ residual
        # Levenberg-Marquardt damping on the diagonal: large lambda behaves like gradient descent,
        # small lambda like Gauss-Newton.
        try:
            step = np.linalg.solve(jtj + lam * np.diag(np.diag(jtj) + 1e-12), jtr)
        except np.linalg.LinAlgError:
            break

        candidate = current + step
        trial = evaluate(set_constants(expression, candidate), X)
        trial_loss = _mse(y, trial)

        if trial_loss < best_loss:
            improvement = best_loss - trial_loss
            current = candidate
            best_loss = trial_loss
            lam = max(lam * 0.5, 1e-12)
            if improvement < tolerance * max(best_loss, 1e-12):
                break
        else:
            lam *= 4.0
            if lam > 1e10:
                break

    tuned = set_constants(expression, current)
    return TuneResult(
        expression=tuned if best_loss < loss_before else expression,
        loss_before=loss_before,
        loss_after=min(best_loss, loss_before),
        iterations=iterations,
        improved=best_loss < loss_before,
        identifiable=identifiable,
        note=rank_note,
    )


def tune_population(
    expressions: list[Node],
    X: np.ndarray,
    y: np.ndarray,
    *,
    indices: list[int] | None = None,
    max_iterations: int = 15,
    max_constants: int = 12,
) -> tuple[list[Node], int]:
    """Tune a subset of the population. Returns the new list and how many were improved.

    `max_constants` skips expressions with more numeric leaves than the budget allows, because the
    Jacobian cost grows with the parameter count and a candidate with twenty free constants is
    usually overfitting rather than modelling.
    """
    out = list(expressions)
    improved = 0
    targets = indices if indices is not None else range(len(expressions))
    for i in targets:
        if n_constants(out[i]) == 0 or n_constants(out[i]) > max_constants:
            continue
        result = levenberg_marquardt(out[i], X, y, max_iterations=max_iterations)
        if result.improved:
            out[i] = result.expression
            improved += 1
    return out, improved

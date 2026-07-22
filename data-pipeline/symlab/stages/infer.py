"""Stage 4: evaluate the discovered Pareto front on data the search never saw.

Three regions, reported separately and never averaged together:

- **train**, where the search optimised. Reported only so the gap to test is visible.
- **test**, held out inside the training support. The ordinary generalisation question.
- **extrapolation**, held out OUTSIDE the support. The question the benchmark literature says every
  method fails, and the one this lab refuses to fold into a single headline number.

Non-finite predictions are counted rather than dropped. An expression that produces infinities on
the extrapolation rows has told you something important about itself, and averaging over the rows
where it happens to behave would hide exactly that.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..model.expr import Node, evaluate, is_valid
from .preprocess import PreparedCase
from .train import TrainedVariant


@dataclass
class RegionScore:
    """How one expression did on one region of the data."""

    n_rows: int
    mse: float | None
    rmse: float | None
    mae: float | None
    r2: float | None
    n_nonfinite: int
    finite_fraction: float


def score_region(expression: Node, X: np.ndarray, y: np.ndarray) -> RegionScore:
    prediction = evaluate(expression, X)
    finite = np.isfinite(prediction)
    n_nonfinite = int(np.sum(~finite))
    if not finite.any():
        return RegionScore(int(len(y)), None, None, None, None, n_nonfinite, 0.0)

    # Scored on the finite rows only, with the non-finite count reported alongside. Silently
    # dropping them would let an expression that diverges on a third of the extrapolation region
    # report a clean error on the rest.
    residual = y[finite] - prediction[finite]
    mse = float(np.mean(residual * residual))
    variance = float(np.var(y[finite]))
    return RegionScore(
        n_rows=int(len(y)),
        mse=mse,
        rmse=float(np.sqrt(mse)),
        mae=float(np.mean(np.abs(residual))),
        r2=float(1.0 - mse / variance) if variance > 0 else None,
        n_nonfinite=n_nonfinite,
        finite_fraction=round(float(np.mean(finite)), 6),
    )


@dataclass
class MemberScores:
    """One Pareto member, scored across every region."""

    index: int
    complexity: int
    train: RegionScore
    test: RegionScore
    extrapolation: RegionScore | None


@dataclass
class VariantInference:
    """Every member of one variant's front, scored."""

    variant_id: str
    members: list[MemberScores]
    best_test_index: int
    best_extrapolation_index: int | None


def run(prepared: PreparedCase, trained: list[TrainedVariant]) -> list[VariantInference]:
    out: list[VariantInference] = []
    for entry in trained:
        members: list[MemberScores] = []
        for index, individual in enumerate(entry.result.pareto):
            expression = individual.expression
            members.append(MemberScores(
                index=index,
                complexity=individual.complexity,
                train=score_region(expression, prepared.X_train, prepared.y_train),
                test=score_region(expression, prepared.X_test, prepared.y_test),
                extrapolation=(
                    score_region(expression, prepared.X_extrap, prepared.y_extrap)
                    if prepared.X_extrap is not None and prepared.y_extrap is not None
                    else None
                ),
            ))

        def _rank(scores: list[MemberScores], attribute: str) -> int | None:
            candidates = [
                (i, getattr(m, attribute))
                for i, m in enumerate(scores)
                if getattr(m, attribute) is not None and getattr(m, attribute).mse is not None
            ]
            if not candidates:
                return None
            return min(candidates, key=lambda pair: pair[1].mse)[0]

        out.append(VariantInference(
            variant_id=entry.variant.id,
            members=members,
            best_test_index=_rank(members, "test") or 0,
            best_extrapolation_index=_rank(members, "extrapolation"),
        ))
    return out

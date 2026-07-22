"""Stage 3: run the search. This is where the ladder rungs actually execute.

One variant equals one search run equals one configuration. Nothing here decides anything about the
science; the decisions live in the variant configurations, which is what makes the ablation
attributable.

The wall-clock of each run is recorded. That is not bookkeeping: the measured cost of a rung is part
of its evaluation, because a selection method that buys quality at 22 times the baseline runtime has
to be compared at equal budget rather than equal generation count, and the benchmark literature
names budget unfairness as one of its standing problems.
"""
from __future__ import annotations

import time
from dataclasses import dataclass


from ..cases.registry import Case, Variant
from ..search.engine import Engine, SearchResult
from ..search.exhaustive import ExhaustiveResult, run_exhaustive
from .feature_extraction import Features
from .preprocess import PreparedCase


@dataclass
class TrainedVariant:
    """One variant's search result, with its measured cost."""

    variant: Variant
    result: SearchResult
    seconds: float


def run(
    prepared: PreparedCase,
    features: Features,
    case: Case,
    *,
    seed: int = 0,
    only: tuple[str, ...] | None = None,
) -> list[TrainedVariant]:
    """Run every variant of a case, in order."""
    out: list[TrainedVariant] = []
    for variant in case.variants:
        if only is not None and variant.id not in only:
            continue
        # The unit-typed rung is only meaningful where units were declared. Running it anyway would
        # produce a chip whose label promises a constraint the data cannot supply.
        if variant.config.unit_typed and not features.units_declared:
            continue
        engine = Engine(
            variant.config,
            input_dims=features.input_dims if features.units_declared else None,
            target_dims=features.target_dims if features.units_declared else None,
        )
        started = time.perf_counter()
        result = engine.run(prepared.X_train, prepared.y_train, seed=seed)
        out.append(TrainedVariant(variant=variant, result=result,
                                  seconds=round(time.perf_counter() - started, 3)))
    return out


def run_certificate(
    prepared: PreparedCase, *, max_nodes: int = 7, primitives: tuple[str, ...] | None = None
) -> ExhaustiveResult:
    """Run the bounded exhaustive search, which is the only rung that can prove a negative."""
    from ..model.expr import PRIMITIVE_SETS

    return run_exhaustive(
        prepared.X_train, prepared.y_train,
        primitives=primitives or PRIMITIVE_SETS["arithmetic"],
        max_nodes=max_nodes,
    )

"""Stage 2: derive what the search needs to know about the data, beyond the rows themselves.

Three things, none of which the search can safely infer for itself:

1. **The input box**, optionally widened. The interval guard rejects candidates that are undefined
   anywhere in this box, so the box IS the definition of "where this model must make sense". Widening
   it beyond the training range is what turns the guard from "safe on this sample" into "safe in the
   neighbourhood we intend to extrapolate into", which is the whole point of the extrapolation split.

2. **The unit declarations**, so the unit-typed rung can constrain generation. A case whose inputs
   are dimensionless gets an honest note rather than a rung that silently does nothing.

3. **A sampling summary** that the app prints next to the result, because a law recovered from data
   sampled over one decade and a law recovered over four decades are not equally supported, and the
   reader cannot tell from the equation alone.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..model.intervals import Interval, from_data
from ..model.units import Dims, format_dims, is_dimensionless
from .preprocess import PreparedCase


@dataclass
class Features:
    """What the search is told about the data before it starts."""

    box: list[Interval]
    input_dims: list[Dims]
    target_dims: Dims
    units_declared: bool
    sampling: list[dict]
    note: str


def run(prepared: PreparedCase, *, interval_margin: float = 0.25) -> Features:
    dataset = prepared.dataset
    box = from_data(prepared.X_train, margin=interval_margin)

    declared = any(not is_dimensionless(d) for d in dataset.input_dims) or not is_dimensionless(
        dataset.target_dims
    )

    sampling: list[dict] = []
    for j, key in enumerate(dataset.input_keys):
        column = prepared.X_train[:, j]
        low, high = float(np.min(column)), float(np.max(column))
        positive = low > 0
        decades = float(np.log10(high / low)) if positive and high > 0 else None
        sampling.append({
            "key": key,
            "display": dataset.input_display[j],
            "unit": dataset.input_units[j],
            "dims": list(dataset.input_dims[j]),
            "dims_label": format_dims(dataset.input_dims[j]),
            "min": low,
            "max": high,
            "mean": float(np.mean(column)),
            "std": float(np.std(column)),
            "decades_spanned": round(decades, 3) if decades is not None else None,
            "guard_low": box[j].lo,
            "guard_high": box[j].hi,
        })

    if declared:
        note = (
            f"Units are declared, so the unit-typed rung constrains generation. Target dimension: "
            f"{format_dims(dataset.target_dims)}."
        )
    else:
        # Saying only "no dimensions declared" reads as an oversight, and on the measured plant
        # cases it is not one. Two distinct reasons a column set is left untyped, both real:
        #
        #   1. An OFFSET scale. Degrees Celsius is not a ratio scale, so multiplying or dividing by
        #      it is not a dimensionally meaningful operation. Typing it as a temperature would let
        #      the rung accept expressions that are unit-consistent on paper and meaningless in fact.
        #   2. Columns that do not SPAN the target. The combined cycle plant records two pressures,
        #      a temperature and a relative humidity, and the target is electrical power. No product
        #      of pressures and dimensionless numbers has the dimensions of power, because the flow
        #      rate that would supply them is not a recorded column. Typing this case would leave
        #      the rung with an empty admissible set, which reads as a failed method rather than as
        #      an incomplete instrument list.
        #
        # So the rung is omitted and the omission is explained, rather than shown as a chip that
        # does nothing or, worse, as a rung that rejects every candidate.
        note = (
            "Inputs carry no declared physical dimensions, so the unit-typed rung is omitted from "
            "this case rather than shown as a chip that does nothing. That is a property of the "
            "instrument list rather than an oversight: a plant records what its sensors report, "
            "which here includes an offset temperature scale and no flow rate, so the recorded "
            "columns cannot be combined into the dimensions of the target at all."
        )

    return Features(
        box=box,
        input_dims=list(dataset.input_dims),
        target_dims=dataset.target_dims,
        units_declared=declared,
        sampling=sampling,
        note=note,
    )

"""The shared expression core.

This package is the only code in the product that runs in more than one lane: the offline pipeline
imports it, the browser lane imports it through Pyodide, and the dormant API would import it too.
That is why it depends on numpy and nothing else, and why nothing in here reads a file, touches the
network, or knows what a case is.

Modules:

- `expr`       the representation: nodes, operators, evaluation, the shared node id space
- `units`      dimensional analysis, used to CONSTRAIN generation, not only to check afterwards
- `intervals`  interval arithmetic guards, so unsound candidates never enter the population
- `scaling`    closed-form linear scaling, the cheapest large quality gain in the classical spine
- `complexity` the three complexity measures and the description-length selection rule
- `latex`      rendering to addressable, theme-safe, line-breakable mathematics
"""
from __future__ import annotations

from . import complexity, expr, intervals, latex, scaling, units
from .expr import OPERATORS, PRIMITIVE_SETS, Node, evaluate, size, walk

__all__ = [
    "complexity",
    "expr",
    "intervals",
    "latex",
    "scaling",
    "units",
    "Node",
    "OPERATORS",
    "PRIMITIVE_SETS",
    "evaluate",
    "size",
    "walk",
]

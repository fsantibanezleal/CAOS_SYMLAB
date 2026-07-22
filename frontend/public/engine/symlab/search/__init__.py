"""The search layer: how candidate expressions are proposed, judged and kept.

Two engines with different guarantees, deliberately not unified:

- `engine.Engine` is the genetic-programming search. Every rung of the classical spine is a switch
  on `SearchConfig`, defaulting OFF, so `SearchConfig()` is a faithful Koza-1992 baseline and the
  `LADDER` dictionary adds exactly one mechanism per step. That is what makes the Experiments page
  an ablation rather than a claim.
- `exhaustive.run_exhaustive` enumerates every structurally distinct expression up to a node bound
  and issues a completeness certificate. It is the only rung here that can prove a negative, and its
  caveats are shipped with it rather than left to the reader.

Everything in this package imports only `model/` and numpy, so the same code runs offline and in the
browser under Pyodide.
"""
from __future__ import annotations

from . import engine, exhaustive, generate, select, tune, variation
from .engine import LADDER, Engine, Individual, SearchConfig, SearchResult
from .exhaustive import Certificate, ExhaustiveResult, run_exhaustive

__all__ = [
    "engine",
    "exhaustive",
    "generate",
    "select",
    "tune",
    "variation",
    "Engine",
    "SearchConfig",
    "SearchResult",
    "Individual",
    "LADDER",
    "run_exhaustive",
    "ExhaustiveResult",
    "Certificate",
]

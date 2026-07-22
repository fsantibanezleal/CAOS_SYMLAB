"""The offline pipeline, as named stages with explicit contracts between them.

The stage NAMES and signatures are frozen by the product archetype; the bodies are the science.
Order: preprocess, feature_extraction, train, infer, evaluate, export.

For a symbolic-regression lab the mapping is:

- `preprocess`         load the dataset, apply the ingestion contract, split train/test/extrapolation
- `feature_extraction` derive the input box, unit declarations and the sampling summary the search needs
- `train`              run the search: this is where the ladder rungs actually execute
- `infer`              evaluate the resulting Pareto front on held-out and extrapolation data
- `evaluate`           score it, including exact-equivalence against a known truth where one exists
- `export`             emit the schema_version 1.0.0 artifact and the case manifest
"""
from __future__ import annotations

from . import evaluate, export, feature_extraction, infer, preprocess, train

STAGES = ("preprocess", "feature_extraction", "train", "infer", "evaluate", "export")

__all__ = ["preprocess", "feature_extraction", "train", "infer", "evaluate", "export", "STAGES"]

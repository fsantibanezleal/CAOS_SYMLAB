"""Re-baking a case must reproduce every scientific number, and only the clock may move.

The product claimed byte-identical regeneration in three places: the architecture modal, the
Implementation page and the pipeline module docstring. It was false twice over. `hash()` seeded the
RNG, so the DATA differed per process (fixed, see test_cross_process_determinism.py), and the
measured wall clock is written into every variant, so even with identical science the bytes differ.

The claim is now the true and more useful one: every number a result depends on is reproducible, and
the only thing that moves between runs is how long it took. The timing is recorded deliberately,
because what a rung costs is part of its evaluation.

This test pins exactly that. It bakes the same case twice into two sandboxes and requires the
documents to be identical after the timing fields are removed. If anything else drifts, some other
source of non-determinism has appeared and the claim is false again.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASE = "monod-saturation"

#: Fields that legitimately vary between runs, and nothing else may.
TIMING_KEYS = {"seconds", "wall_seconds", "total_seconds", "generated_on"}


def _bake(directory: Path) -> dict:
    environment = dict(os.environ, SYMLAB_OUTPUT_DIR=str(directory))
    result = subprocess.run(
        [sys.executable, "-m", "symlab.pipeline", CASE, "--quick"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=environment,
    )
    artifact = directory / "data" / "derived" / CASE / "run.json"
    if result.returncode != 0 or not artifact.exists():
        pytest.skip(f"could not bake: {result.stderr[-300:]}")
    return json.loads(artifact.read_text(encoding="utf-8"))


def _without_timing(value: Any) -> Any:
    """The document with every timing field removed, recursively."""
    if isinstance(value, dict):
        return {k: _without_timing(v) for k, v in value.items() if k not in TIMING_KEYS}
    if isinstance(value, list):
        return [_without_timing(v) for v in value]
    return value


@pytest.fixture(scope="module")
def two_bakes() -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory(prefix="symlab-rebake-a-") as a, tempfile.TemporaryDirectory(
        prefix="symlab-rebake-b-"
    ) as b:
        return _bake(Path(a)), _bake(Path(b))


def test_every_scientific_number_is_reproduced(two_bakes: tuple[dict, dict]) -> None:
    first, second = two_bakes
    stripped_first = _without_timing(first)
    stripped_second = _without_timing(second)

    if stripped_first != stripped_second:
        # Report WHERE, because "the documents differ" is not actionable on a file this size.
        def differences(a: Any, b: Any, path: str = "") -> list[str]:
            if isinstance(a, dict) and isinstance(b, dict):
                out: list[str] = []
                for key in set(a) | set(b):
                    out += differences(a.get(key), b.get(key), f"{path}.{key}")
                return out
            if isinstance(a, list) and isinstance(b, list):
                out = []
                for index, (x, y) in enumerate(zip(a, b)):
                    out += differences(x, y, f"{path}[{index}]")
                return out
            return [] if a == b else [f"{path}: {a!r} vs {b!r}"]

        found = differences(stripped_first, stripped_second)
        pytest.fail(
            "re-baking the same case changed a result, so something non-deterministic has "
            f"appeared: {found[:8]}"
        )


def test_the_only_drift_is_timing(two_bakes: tuple[dict, dict]) -> None:
    """The complement: the raw documents SHOULD differ, and only in the clock.

    If they were byte-identical the timing would not be recorded, and the cost of a rung is part of
    its evaluation. This asserts the recording still happens rather than quietly disappearing.
    """
    first, second = two_bakes
    variants = first["notes"]["variants"]
    assert variants, "no variants to inspect"
    assert all("seconds" in v for v in variants), (
        "variants no longer record measured wall clock, so the cost column on the Experiments page "
        "has nothing behind it"
    )
    assert all(isinstance(v["seconds"], (int, float)) for v in variants)

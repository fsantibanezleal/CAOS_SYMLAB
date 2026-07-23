"""The pipeline must produce the same numbers in a NEW process, not just in this one.

`make_dataset` seeded its RNG with `abs(hash(generator.id))`, and Python randomises string hashing
per process. So every run drew different data from the same declared seed. The docstring one line
above the bug said "Deterministic in (generator.id, n_rows, seed, noise), so a committed artifact
regenerates byte for byte", the Implementation page said regenerating a case produces byte-identical
output, and the footer said every number comes from a seeded offline run. None of it was true.

`semantic_key` had the same defect: it used `hash(bytes)` for the deduplication key, so two
candidates deduplicated against each other in one process and not in the next, which made the
deduplication rung's measured effect a property of interpreter startup.

Nothing caught it because every existing determinism check ran inside ONE process, where the hash
seed is fixed and everything agrees. The check has to cross a process boundary or it is not testing
the thing that breaks.

It also explains a wrong diagnosis: the live lane disagreeing with the offline lane was blamed on
Pyodide's numpy. Pyodide's numpy produces bit-identical streams; the two lanes are two processes.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "data-pipeline"

#: A handful of generators rather than all of them: this spawns real interpreters.
SAMPLED = ["monod-saturation", "stokes-settling", "arrhenius-rate"]

PROBE = """
import sys
sys.path.insert(0, {pipeline!r})
import json
import numpy as np
from symlab.cases.generators import GENERATORS, make_dataset
from symlab.model.expr import semantic_key

out = {{}}
for key in {cases!r}:
    X, y = make_dataset(GENERATORS[key], n_rows=120, seed=0)
    out[key] = {{
        "x_sum": float(np.sum(X)),
        "y_sum": float(np.sum(y)),
        "semantic": semantic_key(y),
    }}
print(json.dumps(out))
"""


def _run_in_fresh_process(hash_seed: str) -> dict:
    """Run the probe with an explicit PYTHONHASHSEED, which is what varies in the wild."""
    import os

    environment = dict(os.environ, PYTHONHASHSEED=hash_seed)
    result = subprocess.run(
        [sys.executable, "-c", PROBE.format(pipeline=str(PIPELINE), cases=SAMPLED)],
        capture_output=True,
        text=True,
        env=environment,
    )
    if result.returncode != 0:
        pytest.skip(f"probe process failed: {result.stderr[-300:]}")
    return json.loads(result.stdout)


def test_sampling_is_identical_under_different_hash_seeds() -> None:
    """The exact condition that was broken.

    PYTHONHASHSEED is random by default, so two ordinary runs differ. Setting it explicitly makes
    the failure reproducible instead of intermittent, which is the difference between a test that
    catches this and one that catches it one time in a thousand.
    """
    first = _run_in_fresh_process("0")
    second = _run_in_fresh_process("12345")

    for case in SAMPLED:
        assert first[case]["x_sum"] == second[case]["x_sum"], (
            f"{case}: the sampled inputs depend on PYTHONHASHSEED, so a committed artifact cannot "
            "be regenerated. Something is seeding an RNG with the builtin hash()."
        )
        assert first[case]["y_sum"] == second[case]["y_sum"], f"{case}: the target depends on the hash seed"


def test_semantic_keys_are_identical_under_different_hash_seeds() -> None:
    """A deduplication key that changes per process makes the dedup rung unmeasurable."""
    first = _run_in_fresh_process("0")
    second = _run_in_fresh_process("999")

    for case in SAMPLED:
        assert first[case]["semantic"] == second[case]["semantic"], (
            f"{case}: the semantic deduplication key depends on PYTHONHASHSEED, so the same two "
            "candidates deduplicate in one process and not in another"
        )


def test_no_module_seeds_randomness_with_the_builtin_hash() -> None:
    """Catch the shape directly, so a new one is refused rather than measured later.

    The builtin `hash` is fine for an in-memory dict. It is never acceptable where the value
    escapes the process: an RNG seed, a cache key written to disk, or an identifier in an artifact.
    """
    import ast

    # Parsed, not grepped. A text scan matches the docstrings that DESCRIBE this bug and reports the
    # explanation as the defect, which is the fastest way to get a guard switched off.
    offenders = []
    for path in (PIPELINE / "symlab").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "hash"
            ):
                offenders.append(f"{path.name}:{node.lineno}")

    assert not offenders, (
        "the builtin hash() is randomised per process and must not seed anything that leaves it "
        f"(an RNG seed, a cache key, an identifier in an artifact): {offenders}"
    )

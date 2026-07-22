"""The exported payload must carry the TYPES its contract declares.

`_plain` normalises the artifact tree for JSON. Its integer branch used to swallow booleans,
because `bool` is a subclass of `int` in Python and `np.bool_` answers to the numpy integer check,
so every boolean in every artifact shipped as 0 or 1 while the TypeScript contract declared
`boolean | null`.

Nothing failed. Almost every consumer tested truthiness, where 1 and `true` behave identically, so
the violation was invisible for as long as nobody compared identity. The first identity comparison
that mattered was `member.units_ok === false`, which is false when the value is 0: the
dimensional-consistency warning could never render, and no test noticed because no test asserted
the TYPE of anything the pipeline wrote.

This file asserts the types.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from symlab.stages.export import _plain


def test_booleans_survive_as_booleans() -> None:
    result = _plain({"yes": True, "no": False})
    assert result["yes"] is True
    assert result["no"] is False
    assert json.dumps(result) == '{"yes": true, "no": false}'


def test_numpy_booleans_survive_as_booleans() -> None:
    result = _plain({"yes": np.bool_(True), "no": np.bool_(False)})
    assert result["yes"] is True
    assert result["no"] is False


def test_integers_are_still_integers() -> None:
    """The fix must not turn every number into a boolean on the way past."""
    result = _plain({"count": 3, "np": np.int64(7)})
    assert result["count"] == 3 and isinstance(result["count"], int)
    assert result["np"] == 7 and not isinstance(result["np"], bool)


def test_non_finite_floats_become_null_rather_than_crashing_the_encoder() -> None:
    result = _plain({"a": float("inf"), "b": float("nan"), "c": 1.5})
    assert result["a"] is None and result["b"] is None
    assert result["c"] == 1.5


@pytest.mark.parametrize(
    "path",
    [
        ("notes", "ground_truth_known"),
        ("engine", "deterministic"),
    ],
)
def test_declared_boolean_fields_are_boolean_in_a_real_artifact(path: tuple[str, ...]) -> None:
    """The end-to-end check, on whatever the pipeline last wrote.

    A unit test on the normaliser proves the function; this proves the artifact. Skips when nothing
    has been baked, because derived data is produced offline rather than committed by the test run.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "data" / "derived"
    runs = sorted(root.glob("*/run.json"))
    if not runs:
        pytest.skip("no baked artifact to inspect")

    document = json.loads(runs[-1].read_text(encoding="utf-8"))
    value = document
    for key in path:
        if key not in value:
            pytest.skip(f"{'.'.join(path)} absent from this artifact")
        value = value[key]

    assert isinstance(value, bool), (
        f"{'.'.join(path)} is {type(value).__name__} ({value!r}) in {runs[-1].parent.name}; the "
        "contract declares a boolean. Re-bake after the _plain fix."
    )

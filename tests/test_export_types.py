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


def test_small_magnitudes_survive_the_rounding() -> None:
    """A very small number must not be published as zero.

    `round(v, 8)` collapsed everything below 5e-9 to exactly 0.0, so a mean squared error of
    6.1e-12 shipped as "0.0" and an R-squared of 0.999999998 shipped as "1.0". Both are claims of
    an EXACT fit, and this lab's entire argument turns on the difference between a very good fit
    and the right answer. Worse, a method reporting zero error alongside "structure not recovered"
    reads as a contradiction rather than as the finding it is.
    """
    result = _plain({
        "tiny_loss": 6.068236770292292e-12,
        "near_one": 0.999999998209809,
        "ordinary": 1.23456789012345,
        "large": 1234567.891011,
    })
    assert result["tiny_loss"] != 0.0
    assert result["tiny_loss"] == pytest.approx(6.068236770e-12, rel=1e-9)
    assert result["near_one"] != 1.0
    assert result["near_one"] == pytest.approx(0.9999999982, rel=1e-9)
    assert result["ordinary"] == pytest.approx(1.23456789, rel=1e-8)
    assert result["large"] == pytest.approx(1234567.891, rel=1e-9)


def test_exact_zero_is_still_exactly_zero() -> None:
    """The fix must not turn a genuine zero into a near-zero."""
    result = _plain({"zero": 0.0, "negative_zero": -0.0})
    assert result["zero"] == 0.0
    assert result["negative_zero"] == 0.0


def test_a_zero_loss_never_sits_beside_a_failed_recovery() -> None:
    """End to end: the one combination that cannot both be true.

    A loss of exactly 0.0 IS legitimate when the search recovered the law: an algebraically
    identical expression evaluates to identical floats, so the residual really is zero. What cannot
    be true is zero error alongside "structure not recovered", and that is precisely what the old
    decimal rounding manufactured: a mean squared error of 6.1e-12 published as 0.0 next to a
    verdict saying the law was not found. A reader sees a contradiction and stops trusting both
    numbers, when the real finding was a very good fit with the wrong structure.

    Skips when nothing is baked. Does not skip when an artifact contradicts itself.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "data" / "derived"
    runs = sorted(root.glob("*/run.json"))
    if not runs:
        pytest.skip("no baked artifact to inspect")

    contradictions = []
    for path in runs:
        document = json.loads(path.read_text(encoding="utf-8"))
        for variant in document.get("notes", {}).get("variants", []):
            equivalence = variant.get("score", {}).get("equivalence")
            if not equivalence:
                continue
            symbolic, numerical = equivalence.get("symbolic"), equivalence.get("numerical")
            if symbolic is None and numerical is None:
                continue
            recovered = bool(symbolic if symbolic is not None else numerical)
            if recovered:
                continue
            selected = variant.get("selected_index", 0)
            members = variant.get("pareto", [])
            if selected >= len(members):
                continue
            member = members[selected]
            if member.get("loss_train") == 0.0:
                contradictions.append(
                    f"{path.parent.name}/{variant['id']} reports zero loss and no recovery"
                )

    assert not contradictions, (
        "an artifact cannot report a mathematically exact fit AND a failure to recover the law: "
        f"{contradictions[:5]}. Re-bake after the significant-digit fix."
    )

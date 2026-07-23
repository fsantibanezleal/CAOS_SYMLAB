"""Every variant must export the member it says it selected, and only that member.

The exporter capped each Pareto front at twelve members and then clamped the selected index into
that slice with `min(index, len - 1)`. On a front longer than twelve where selection landed past the
cap, the clamp did not fail: it silently picked a different member, and the equation, tree and
validation arrays were built from THAT one while `score` (description length, complexity, test R2,
recovery verdict) still described the model selection actually chose.

The result was a variant panel showing one model's formula above another model's numbers, with
nothing on screen to indicate it. Ten variants across the committed corpus were in that state.

These checks are cheap, run over whatever artifacts exist, and would have caught it on the first
bake that produced a long front.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = sorted((ROOT / "data" / "derived").glob("*/run.json"))


def _variants(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    for variant in payload.get("notes", {}).get("variants", []):
        yield variant


pytestmark = pytest.mark.skipif(not ARTIFACTS, reason="no baked artifacts to check")


@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.parent.name)
def test_selected_index_is_inside_the_exported_front(path: Path):
    for variant in _variants(path):
        front = variant.get("pareto", [])
        if not front:
            continue
        index = variant.get("selected_index")
        assert index is not None and 0 <= index < len(front), (
            f"{path.parent.name}/{variant['id']}: selected_index {index} is outside the "
            f"{len(front)} exported members. The app reads the published model at this position."
        )


@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.parent.name)
def test_the_two_selected_indices_agree(path: Path):
    """`variant.selected_index` and `score.selected_index` must mean the same position.

    They did not. One was remapped into the exported slice and the other was the raw index into the
    full front, both spelled `selected_index`, and different readers picked different ones.
    """
    for variant in _variants(path):
        front = variant.get("pareto", [])
        score = variant.get("score") or {}
        if not front or "selected_index" not in score:
            continue
        assert score["selected_index"] == variant["selected_index"], (
            f"{path.parent.name}/{variant['id']}: score.selected_index "
            f"{score['selected_index']} disagrees with variant.selected_index "
            f"{variant['selected_index']}. Re-bake: these are the same fact."
        )


@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.parent.name)
def test_the_published_complexity_matches_the_selected_member(path: Path):
    """The strongest form of the check: the score must describe the member that shipped.

    Complexity is the field to test on, because it is recorded in both places, is an integer, and
    differs between front members by construction. If the exporter ever again publishes one member's
    expression beside another member's numbers, this is what catches it.
    """
    for variant in _variants(path):
        front = variant.get("pareto", [])
        score = variant.get("score") or {}
        if not front or score.get("selected_complexity") is None:
            continue
        member = front[variant["selected_index"]]
        assert member["complexity"] == score["selected_complexity"], (
            f"{path.parent.name}/{variant['id']}: the exported member at the selected index has "
            f"complexity {member['complexity']}, but the score reports "
            f"{score['selected_complexity']}. The equation and the numbers describe different models."
        )

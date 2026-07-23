"""The recovery verdict is decided twice, in two languages, and must not drift.

`stages/evaluate.py :: Equivalence.recovered` is the lab's rule: trust the symbolic test where it
decided, fall back to the numerical one where it did not. That property is what the manifest records
per variant as `exact_recovery`, and what the summary counts.

The artifact's per-variant `equivalence` block does NOT carry it. It ships the three test results and
leaves the verdict to be re-derived, and `render/ExpressionPanel.tsx` re-derives it:

    const recovered = eq ? (eq.symbolic !== null ? eq.symbolic : eq.numerical) : null;

which is the same rule written a second time in TypeScript. Everywhere else this product refuses that
arrangement: term colours are assigned in Python and exported so the equation, the tree and the
contribution chart cannot disagree. Here two implementations decide the single most important claim
the lab makes, and nothing compared them.

Exporting the field would be the better fix and costs a full re-bake, so until then this is the
check: for every variant of every case, the rule the app applies to the artifact must produce the
verdict the pipeline recorded in the manifest. If a future edit changes one side, this fails.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = sorted((ROOT / "data" / "derived").glob("*/run.json"))

pytestmark = pytest.mark.skipif(not ARTIFACTS, reason="nothing baked yet")


def _app_rule(equivalence: dict | None):
    """Exactly what ExpressionPanel.tsx computes, transcribed."""
    if equivalence is None:
        return None
    symbolic = equivalence.get("symbolic")
    if symbolic is not None:
        return bool(symbolic)
    numerical = equivalence.get("numerical")
    return bool(numerical) if numerical is not None else False


@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.parent.name)
def test_the_app_rule_reproduces_the_recorded_verdict(path: Path):
    case_id = path.parent.name
    manifest_path = ROOT / "manifests" / f"{case_id}.json"
    if not manifest_path.exists():
        pytest.skip(f"no manifest for {case_id}")

    recorded = {
        v["id"]: v.get("exact_recovery")
        for v in json.loads(manifest_path.read_text(encoding="utf-8")).get("variants", [])
    }
    payload = json.loads(path.read_text(encoding="utf-8"))

    for variant in payload.get("notes", {}).get("variants", []):
        name = variant["id"]
        if name not in recorded or recorded[name] is None:
            continue  # no truth to compare against; recovery is not checkable and says so
        derived = _app_rule((variant.get("score") or {}).get("equivalence"))
        assert derived == recorded[name], (
            f"{case_id}/{name}: the app's rule gives {derived!r} and the pipeline recorded "
            f"{recorded[name]!r}. The recovery verdict is implemented twice and they have drifted."
        )


@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.parent.name)
def test_the_summary_counts_match_the_per_variant_verdicts(path: Path):
    """The headline rate a reader sees must be the sum of the verdicts beside it."""
    case_id = path.parent.name
    manifest_path = ROOT / "manifests" / f"{case_id}.json"
    if not manifest_path.exists():
        pytest.skip(f"no manifest for {case_id}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    per_variant = [v.get("exact_recovery") for v in manifest.get("variants", [])]
    scored = [v for v in per_variant if v is not None]
    if not scored:
        return

    summary = json.loads(path.read_text(encoding="utf-8"))["notes"]["summary"]
    assert summary["exact_recoveries"] == sum(1 for v in scored if v), (
        f"{case_id}: summary reports {summary['exact_recoveries']} recoveries and the per-variant "
        f"verdicts count {sum(1 for v in scored if v)}."
    )

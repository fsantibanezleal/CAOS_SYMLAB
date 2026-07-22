"""No committed artifact may be a reduced-budget run.

`--quick` exists so a smoke run finishes in seconds. It writes to the SAME tree the published
artifacts live in, so any quick run, from a test or from a hand-typed command, silently replaces a
full-budget result with one that used a fifth of the population and a third of the variants. The
file looks normal. The app renders it. Every number on the page is then a number the published
budget did not produce.

This has already happened here: the committed `monod-saturation` artifact was a quick run, at
population 60 with 3 variants instead of 300 with 9. It has happened before elsewhere in this line,
where a pytest run clobbered a committed bake and two releases shipped it.

Two defences, both here:

- `tests/test_contract_conformance.py` writes into a sandbox via `SYMLAB_OUTPUT_DIR`, so the suite
  cannot do it at all.
- this file fails when an artifact on disk carries a budget the registry does not declare, so a
  hand-typed `--quick` cannot reach a release either.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"

sys.path.insert(0, str(ROOT / "data-pipeline"))

ARTIFACTS = sorted(DERIVED.glob("*/run.json"))


def _expected_budgets() -> dict[str, tuple[int, int]]:
    """case id -> (population, variant count) the registry declares.

    Expanded suite cases inherit their parent's variants, so the suite entry answers for them.
    """
    from symlab.cases.registry import list_cases
    from symlab.pipeline import expand_suites

    out: dict[str, tuple[int, int]] = {}
    for case in expand_suites(list_cases()):
        populations = {
            v.config.population for v in case.variants if v.method == "gp" and v.config.population
        }
        if populations:
            out[case.id] = (max(populations), len(case.variants))
    return out


@pytest.mark.skipif(not ARTIFACTS, reason="nothing baked yet")
@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.parent.name)
def test_artifact_used_the_published_population(path: Path) -> None:
    """The hard one: a budget the registry never declared means a --quick run got committed.

    Kept separate from the variant-count check below, because the two mean different things and a
    noisy failure of one would mask the other. This is the defect; that one is staleness.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    case_id = document["notes"]["case_id"]
    expected = _expected_budgets().get(case_id)
    if expected is None:
        pytest.skip(f"{case_id} is not in the registry, so there is no declared budget")

    expected_population, _ = expected
    populations = {
        v["config"]["population"]
        for v in document["notes"]["variants"]
        if (v.get("method") or "gp") == "gp"
    }
    populations.discard(None)

    assert populations and max(populations) >= expected_population, (
        f"{case_id} was baked at population {max(populations) if populations else 'none'} and the "
        f"registry declares {expected_population}. A --quick run is sitting in the published tree: "
        "re-bake this case at the real budget before release."
    )


@pytest.mark.skipif(not ARTIFACTS, reason="nothing baked yet")
@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.parent.name)
def test_artifact_carries_every_declared_variant(path: Path) -> None:
    """Staleness rather than a wrong budget: the registry gained a configuration this run predates.

    Failing is correct. An artifact missing a variant renders a case whose method list disagrees
    with every other case, and the ablation table silently summarises that rung over fewer cases
    than the reader is told.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    case_id = document["notes"]["case_id"]
    expected = _expected_budgets().get(case_id)
    if expected is None:
        pytest.skip(f"{case_id} is not in the registry")

    _, expected_variants = expected
    present = len(document["notes"]["variants"])
    assert present >= expected_variants, (
        f"{case_id} carries {present} variants and the registry declares {expected_variants}. "
        "This artifact predates a configuration that now exists; re-bake it."
    )


def test_the_pipeline_output_tree_is_overridable() -> None:
    """The mechanism the sandboxing depends on.

    Without it, any test that regenerates an artifact has to write into the canonical tree, and
    "just be careful" is not a control.
    """
    source = (ROOT / "data-pipeline" / "symlab" / "pipeline.py").read_text(encoding="utf-8")
    assert "SYMLAB_OUTPUT_DIR" in source, (
        "the pipeline no longer honours an output override, so a test cannot avoid writing over "
        "the committed artifacts"
    )


def test_the_conformance_test_uses_the_sandbox() -> None:
    """Named directly, because this is the test that caused the damage."""
    source = (ROOT / "tests" / "test_contract_conformance.py").read_text(encoding="utf-8")
    assert "SYMLAB_OUTPUT_DIR" in source, (
        "test_contract_conformance bakes a case; it must write into a sandbox, not into "
        "data/derived/"
    )

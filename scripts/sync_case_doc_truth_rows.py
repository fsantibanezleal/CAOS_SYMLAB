"""Reconcile the truth and regime rows in docs/cases/*.md against the code.

Those rows are the one part of a hand-authored case page that is a mechanical fact rather than
prose, and they went stale the moment truth nodes were added for six generators and seventeen
Feynman laws: pages still read "NO, no truth_node is defined" for cases that now carry a verified
one. Documentation that contradicts the artifact is worse than documentation that is missing,
because a reader has no way to tell which one is lying.

So they are generated rather than maintained. Run this after any change to the truth coverage; it
is checked by tests/test_case_docs_match_code.py, which fails when a page disagrees with the code.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

from symlab.cases.generators import GENERATORS  # noqa: E402
from symlab.cases.physics_truths import FEYNMAN_TRUTHS, INEXPRESSIBLE  # noqa: E402
from symlab.cases.registry import list_cases  # noqa: E402
from symlab.pipeline import expand_suites  # noqa: E402

DOCS = ROOT / "docs" / "cases"

TRUTH_ROW = re.compile(r"^\| Machine-comparable truth \|.*\|$", re.M)
REGIME_ROW = re.compile(r"^\| Recovery regime \|.*\|$", re.M)


def truth_state(case_id: str) -> tuple[bool, str, str]:
    """(has truth, regime, a short note) for one registry case id."""
    cases = {c.id: c for c in list_cases()}
    case = cases.get(case_id)
    if case is None:
        return False, "unknown", "case id not in the registry"

    if case.is_generator:
        generator = GENERATORS[case.loader.split(":", 1)[1]]
        if generator.truth_node is not None:
            return True, generator.regime, "verified against its own generator to 1e-9 relative"
        return False, generator.regime, "no truth node; see the generator for the recorded reason"

    if case.loader == "pmlb:feynman":
        expressible = sum(1 for c in expand_suites([case]) if _feynman_name(c) in FEYNMAN_TRUTHS)
        blocked = sum(1 for c in expand_suites([case]) if _feynman_name(c) in INEXPRESSIBLE)
        return (
            expressible > 0,
            "structure",
            f"{expressible} of {expressible + blocked} expanded problems carry a verified law; "
            f"{blocked} cannot be written in this operator set",
        )

    return False, "unknown", "loaded from a file; no in-repo expression to compare against"


def _feynman_name(case) -> str:
    return case.loader.split(":", 1)[1] if ":" in case.loader else ""


def main() -> int:
    changed = []
    for path in sorted(DOCS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^\| Case id \| `([^`]+)` \|$", text, re.M)
        if not match:
            continue
        case_id = match.group(1)
        has_truth, regime, note = truth_state(case_id)

        truth_cell = (
            f"| Machine-comparable truth | {'YES' if has_truth else 'NO'}, {note} |"
        )
        regime_cell = f"| Recovery regime | `{regime}` |"

        updated = TRUTH_ROW.sub(lambda _: truth_cell, text, count=1)
        updated = REGIME_ROW.sub(lambda _: regime_cell, updated, count=1)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(path.name)

    print(f"synced {len(changed)} case pages: {', '.join(changed) if changed else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

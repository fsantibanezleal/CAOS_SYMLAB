"""Regenerate the headline measurement table in README.md from the baked artifact.

The README leads with a measured table rather than a feature list, which is the right call and also
the easiest thing in the repository to leave stale. Every number in it comes from one artifact, and
that artifact is re-baked whenever the engine, the sampling or the export changes. A hand-copied
table survives all of those silently.

So it is generated, between markers, by the same pattern that owns the counts in `docs/cases.md`.
`tests/test_readme_describes_this_product.py` fails when the file disagrees with the artifact.

Run after a bake:
    python scripts/sync_readme_headline.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

#: The case the README leads with. Chosen because it is the clearest instance of the product's
#: whole argument: a near-perfect fit from two unrelated families, and neither recovers the law.
CASE = "feynman-i_6_2a"

START = "<!-- headline:start -->"
END = "<!-- headline:end -->"

#: Rungs worth showing. The full ladder is nine rows and the point is made by four.
SHOWN = ("r1-koza-baseline", "r2-linear-scaling", "r7-deduplication", "sparse-regression")


def _format_r2(value: float | None) -> str:
    """Mirror the app's formatter: never render a near-one as exactly 1.

    `toFixed(5)` printed 0.999999998 as "1.00000" beside "structure not recovered", which reads as a
    contradiction. The README must not reintroduce that.
    """
    if value is None:
        return "n/a"
    if value == 1:
        return "1"
    if 1 - 1e-5 < value < 1:
        return f"1 - {1 - value:.1e}"
    return f"{value:.6f}"


def main() -> int:
    artifact = ROOT / "data" / "derived" / CASE / "run.json"
    if not artifact.exists():
        print(f"skipped: {artifact} not baked yet")
        return 0

    document = json.loads(artifact.read_text(encoding="utf-8"))
    variants = {v["id"]: v for v in document["notes"]["variants"]}

    rows = [
        "| Family | Configuration | R2 (test) | Recovered | Seconds |",
        "|---|---|---|---|---|",
    ]
    for rung in SHOWN:
        variant = variants.get(rung)
        if variant is None:
            continue
        score = variant["score"]
        equivalence = score.get("equivalence")
        if not equivalence or (equivalence["symbolic"] is None and equivalence["numerical"] is None):
            recovered = "not checkable"
        else:
            verdict = (
                equivalence["symbolic"]
                if equivalence["symbolic"] is not None
                else equivalence["numerical"]
            )
            recovered = "yes" if verdict else "no"
        family = "sparse regression" if (variant.get("method") or "gp") != "gp" else "genetic programming"
        rows.append(
            f"| {family} | {variant['label_en']} | {_format_r2(score.get('best_test_r2'))} "
            f"| {recovered} | {score['seconds']:.2f} |"
        )

    block = "\n".join([START, "", *rows, "", END])

    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("README has no headline markers; add them around the table first")
        return 1
    head = text[: text.index(START)]
    tail = text[text.index(END) + len(END) :]
    updated = head + block + tail
    if updated != text:
        README.write_text(updated, encoding="utf-8")
        print(f"README headline table regenerated from {CASE}")
    else:
        print("README headline table already current")
    return 0


if __name__ == "__main__":
    sys.exit(main())

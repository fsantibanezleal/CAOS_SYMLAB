"""Re-derive the published cost multiples from the committed manifests.

Four surfaces quote what each rung costs relative to the Koza baseline: the GPU-lane guide, the
Methodology page, a docstring in `SearchHistory.tsx`, and `requirements-gpu.txt`, which uses them to
argue that no GPU step would help. They were measured by hand once, and a number measured by hand
once is a number that goes stale the next time the ladder changes. It changed: r6 now carries
multi-objective survival and injects an age-0 individual per generation, so its cost is not what it
was when those figures were written.

So they are computed here instead. Run this after any bake and reconcile the four surfaces against
what it prints.

The multiples are CUMULATIVE by construction, because a rung inherits every mechanism below it. That
is worth stating wherever they are quoted: the isolated cost of one mechanism is a different
measurement, taken at a deliberately small budget, and the two must not be presented as the same
number.

Usage:
    .venv/Scripts/python.exe scripts/measure_rung_costs.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
BASELINE = "r1-koza-baseline"


def main() -> int:
    artifacts = sorted(DERIVED.glob("*/run.json"))
    if not artifacts:
        print("no artifacts in data/derived", file=sys.stderr)
        return 1

    # ratio[variant_id] = [seconds_variant / seconds_baseline, one per case that has both]
    ratios: dict[str, list[float]] = {}
    absolute: dict[str, list[float]] = {}
    cases_used = 0

    for path in artifacts:
        payload = json.loads(path.read_text(encoding="utf-8"))
        variants = payload.get("notes", {}).get("variants", [])
        seconds = {v["id"]: v.get("seconds") for v in variants}
        base = seconds.get(BASELINE)
        for name, value in seconds.items():
            if isinstance(value, (int, float)):
                absolute.setdefault(name, []).append(float(value))
        if not isinstance(base, (int, float)) or base <= 0:
            continue
        cases_used += 1
        for name, value in seconds.items():
            if name == BASELINE or not isinstance(value, (int, float)):
                continue
            ratios.setdefault(name, []).append(float(value) / float(base))

    print(f"{len(artifacts)} artifacts, {cases_used} with a usable {BASELINE} time\n")
    print(f"{'variant':28s} {'n':>3s} {'median x base':>14s} {'min':>8s} {'max':>9s} {'median s':>10s}")
    print("-" * 76)
    for name in sorted(ratios, key=lambda k: statistics.median(ratios[k])):
        r = ratios[name]
        secs = absolute.get(name, [])
        print(
            f"{name:28s} {len(r):3d} {statistics.median(r):14.1f} "
            f"{min(r):8.1f} {max(r):9.1f} {statistics.median(secs):10.2f}"
        )

    base_secs = absolute.get(BASELINE, [])
    if base_secs:
        print(f"\n{BASELINE:28s} {len(base_secs):3d} {1.0:14.1f} "
              f"{1.0:8.1f} {1.0:9.1f} {statistics.median(base_secs):10.2f}")

    print(
        "\nThese are CUMULATIVE: a rung inherits every mechanism below it, so the multiple for r7 is\n"
        "the cost of everything up to and including deduplication, not the cost of deduplication.\n"
        "Quote them that way, and keep any isolated single-mechanism figure clearly separate."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

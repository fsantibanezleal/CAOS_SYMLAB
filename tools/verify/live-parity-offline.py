"""The offline half of the live-lane parity check.

Runs exactly what `search.worker.ts` runs, at the same case, seed and budget, in the local Python
environment. The browser half prints what it rendered; comparing the two answers the question the
Live tab asserts and nothing was verifying: are these really the same engine, or only the same
source?

The engine is seeded and deterministic, so agreement means the SAME expression, not a similar one.
A divergence would mean Pyodide's numpy differs from the local one somewhere that matters, and the
site would be publishing a number a reader cannot reproduce.

Usage, from the repository root:
    python tools/verify/live-parity-offline.py --case monod-saturation
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "data-pipeline"))

from symlab.cases.generators import GENERATORS, make_dataset  # noqa: E402
from symlab.model.expr import to_infix  # noqa: E402
from symlab.search.engine import LADDER, Engine  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default="monod-saturation")
    parser.add_argument("--population", type=int, default=80)
    parser.add_argument("--generations", type=int, default=12)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    generator = GENERATORS.get(args.case) or GENERATORS["monod-saturation"]

    # These three lines mirror search.worker.ts exactly. If that file changes, this must change with
    # it, and the comparison is meaningless otherwise.
    X, y = make_dataset(generator, n_rows=240, seed=args.seed)
    config = replace(
        LADDER["r4-multi-objective"],
        population=args.population,
        generations=args.generations,
        primitive_set=generator.suggested_primitives,
    )

    started = time.perf_counter()
    result = Engine(config).run(X, y, seed=args.seed)
    elapsed = time.perf_counter() - started
    best = result.best

    print(json.dumps({
        "case": args.case,
        "budget": {
            "population": args.population,
            "generations": args.generations,
            "seed": args.seed,
        },
        "offline": {
            "infix": to_infix(best.expression, generator.input_keys),
            "complexity": int(best.complexity),
            "mse": float(best.loss),
            "seconds": round(elapsed, 3),
            "front_size": len(result.pareto),
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

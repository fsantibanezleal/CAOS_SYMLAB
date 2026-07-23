"""Which lane a case can run in, decided by measurement rather than by assertion.

The app offers two ways to see a search: REPLAY, which renders a committed artifact, and LIVE, which
runs the engine in the reader's browser through Pyodide and shows the result of a search that has
never been run before. Every case can be replayed. Not every case can be run live, and the honest
version of the Live tab has to say which and why.

What actually decides it here is narrower than it looks, and it is not performance:

  **The browser must be able to produce the data.** The live lane ships the `symlab` modules and
  regenerates the inputs in-process from a first-principles generator. A case loaded from a file
  cannot run live, because the file is not shipped: the flotation ARFF alone is 737,453 rows, and
  publishing the raw sources beside the app to enable an in-browser re-fit would multiply the
  download by orders of magnitude for a feature nobody asked for. So a case runs live if and only if
  it has a generator.

That is the whole rule, and it is stated that way because the previous version of this module was
not. It scored `pure_python`, a Pyodide-safe wheel set, a 1500 ms runtime budget and a 256 KiB trace
budget, and declared in its own docstring that the verdict "goes into the manifest, and CI fails on
mislabeling. This is a MEASUREMENT, never a hand-wave." None of that was true. The function had zero
callers anywhere in the repository, `build_manifest` hardcoded `"lane": "precompute"` for every case,
and the CI check compared `manifest["gate"]["lane"]` against `manifest["lane"]` where `gate` was
never written, so the comparison passed vacuously on all 39 artifacts. Every number in it was also
wrong for this product: numpy is the only wheel and every lane uses it, and the smallest committed
artifact is several times the 256 KiB budget it would have failed everything against.

The runtime budget is gone rather than corrected. The live lane deliberately runs a REDUCED
configuration (240 rows, a small population, few generations) precisely so it returns inside an
interaction budget, so gating cases on the wall-clock of the full offline bake would have measured
the wrong search and excluded cases that run live perfectly well.
"""
from __future__ import annotations

#: The wheel set the live lane may import. Recorded because it is a real constraint on what the
#: engine may ever depend on, not because any case has yet come close to violating it.
LIVE_WHEELS: set[str] = {"numpy"}


def classify_lane(*, has_generator: bool, wheels: set[str] | None = None) -> dict:
    """The lane verdict for one case, with the reasons that produced it.

    `has_generator` is the question that decides it: can the browser build this case's inputs from
    code that ships, without downloading the source data.
    """
    reasons: list[str] = []
    live = True

    if not has_generator:
        live = False
        reasons.append(
            "no first-principles generator: the browser cannot reproduce this data without the "
            "source file, which is not shipped"
        )

    extra = sorted(set(wheels or set()) - LIVE_WHEELS)
    if extra:
        live = False
        reasons.append(f"wheels outside the Pyodide-safe set: {extra}")

    return {
        "lane": "live" if live else "precompute",
        "has_generator": has_generator,
        "wheels": sorted(wheels or LIVE_WHEELS),
        "reasons": reasons,
    }

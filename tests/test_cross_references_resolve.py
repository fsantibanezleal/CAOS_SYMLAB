"""Every id one part of the repository names in another must actually exist.

A dangling cross-reference is invisible. Nothing imports it, nothing renders it, no test touches it,
and it reads as a fact right up until a reader tries to follow it. Five of the seven generators that
declared a `real_data_twin` named a case id that exists in no registry and no source table
(`penicillin-monod`, `geomet-bond` twice, `gpdd-density-dependence`, `lynx-hare-lotka-volterra`), and
the Lotka-Volterra caveats told a reader that the predator equation and the conserved quantity
"ship as their own variants" when neither generator was ever written.

Those are claims about what this lab contains, made in the place a reader is most likely to believe
them. This is the cheap check that keeps them true.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

from symlab.cases.generators import GENERATORS  # noqa: E402
from symlab.cases.registry import list_cases  # noqa: E402
from symlab.io.sources import SOURCES  # noqa: E402


def _known_ids() -> set[str]:
    """Everything a cross-reference is allowed to point at."""
    return {case.id for case in list_cases()} | set(SOURCES) | set(GENERATORS)


def test_every_real_data_twin_resolves():
    known = _known_ids()
    dangling = {
        generator.id: generator.real_data_twin
        for generator in GENERATORS.values()
        if generator.real_data_twin and generator.real_data_twin not in known
    }
    assert not dangling, (
        f"{len(dangling)} generator(s) name a real-data twin that exists nowhere: {dangling}. "
        "Point it at a real case or source id, or set it to None. A twin a reader cannot open is a "
        "claim about this repository that is not true of it."
    )


def test_every_generator_the_registry_names_exists():
    missing = sorted(
        case.loader.split(":", 1)[1]
        for case in list_cases()
        if case.is_generator and case.loader.split(":", 1)[1] not in GENERATORS
    )
    assert not missing, f"the registry declares generator cases with no generator: {missing}"


def test_no_generator_promises_a_variant_that_does_not_exist():
    """Catch the specific phrasing that was false, in the specific field a reader reads.

    Narrow on purpose. A general prose check would either miss the claim or fire on every sentence
    containing the word; this asserts that a caveat which says something ships as its own variant
    is accompanied by a generator that ships it.
    """
    promises = [
        (generator.id, caveat)
        for generator in GENERATORS.values()
        for caveat in generator.caveats
        if "ships as its own variant" in caveat or "ship as their own variants" in caveat
    ]
    unbacked = [
        (case_id, caveat) for case_id, caveat in promises
        # A promise is only credible if this generator has siblings sharing its id stem.
        if sum(1 for other in GENERATORS if other.startswith(case_id.split("-")[0])) < 2
    ]
    assert not unbacked, (
        f"caveat(s) promise a sibling variant that is not registered: {unbacked}. "
        "Either write the generator or describe the formulation as not implemented."
    )

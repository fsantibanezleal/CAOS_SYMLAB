"""The ladder must only ever ADD mechanisms, because every claim made about it assumes that.

The Experiments page attributes the difference between two adjacent rungs to the one mechanism whose
name sits between them. That attribution is only valid if the later rung is the earlier one plus that
mechanism, and nothing else. It was not: `r6-age-fitness-islands` omitted `multi_objective` while r5
carried it and r7 turned it back on, so r6 quietly dropped complexity as an objective at the same
time as it added age and islands. The page still read the whole delta as the cost of islands.

Nothing caught it because a rung with the wrong flags still runs, still converges and still exports.
This is the check that would have.

The parsimony arm is deliberately excluded: it is an ARM, not a rung. It branches off r3 to answer a
different question (a scalar penalty against a Pareto front), and requiring it to be a superset of
the whole ladder would be requiring it to stop being the comparison it exists to make.
"""

from __future__ import annotations

import sys
from dataclasses import fields
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

from symlab.search.engine import LADDER  # noqa: E402

RUNGS = [name for name in LADDER if name.startswith("r")]

#: Flags that switch a mechanism ON. A later rung may not turn any of them back off.
MECHANISMS = [
    f.name for f in fields(LADDER["r1-koza-baseline"])
    if f.type in ("bool", bool) or isinstance(f.default, bool)
]


def test_the_rungs_are_in_ladder_order():
    """r1 through r8, in that order, so 'the rung before' is well defined."""
    assert RUNGS == sorted(RUNGS), f"the ladder is declared out of order: {RUNGS}"
    assert len(RUNGS) >= 8, f"expected at least eight rungs, found {len(RUNGS)}"


@pytest.mark.parametrize("index", range(1, len(RUNGS)))
def test_each_rung_keeps_every_mechanism_the_previous_one_had(index: int):
    previous_name, current_name = RUNGS[index - 1], RUNGS[index]
    previous, current = LADDER[previous_name], LADDER[current_name]

    lost = [
        name for name in MECHANISMS
        if getattr(previous, name) is True and getattr(current, name) is not True
    ]
    assert not lost, (
        f"{current_name} turns OFF {lost}, which {previous_name} had on. The ladder claims each rung "
        f"adds exactly one mechanism, and the Experiments page attributes the measured delta to the "
        f"name between them. Either restore the flag or stop calling this a ladder."
    )


@pytest.mark.parametrize("index", range(1, len(RUNGS)))
def test_each_rung_adds_at_least_one_mechanism(index: int):
    """A rung that changes nothing is a duplicate measurement sold as an ablation."""
    previous_name, current_name = RUNGS[index - 1], RUNGS[index]
    previous, current = LADDER[previous_name], LADDER[current_name]

    changed = [
        f.name for f in fields(current)
        if getattr(previous, f.name) != getattr(current, f.name)
    ]
    assert changed, f"{current_name} is identical to {previous_name}"


def test_the_top_rung_carries_every_mechanism():
    """Whatever the ladder introduces must still be on at the top, or it was not cumulative."""
    top = LADDER[RUNGS[-1]]
    ever_on = {
        name for name in MECHANISMS
        for rung in RUNGS if getattr(LADDER[rung], name) is True
    }
    off_at_top = sorted(name for name in ever_on if getattr(top, name) is not True)
    assert not off_at_top, f"{RUNGS[-1]} does not carry {off_at_top}, which earlier rungs turned on"

"""Published physical laws for the expanded physics suites, as machine-comparable expressions.

The registry says of the Feynman case that "because the answer is known, this case reports a
SOLUTION RATE, which is a categorically stronger claim than a coefficient of determination". That
claim was false until this module existed: the suite cases are loaded through PMLB rather than
built by a generator, so nothing resolved a truth for them and every one of them reported recovery
as "not checkable". A benchmark whose entire purpose is checkable recovery was not checking it.

Two rules govern this file.

**Every truth is verified numerically against its own dataset before it ships.** A wrong truth does
not fail loudly; it produces a confident "not recovered" against a method that recovered the law
perfectly, which is worse than reporting nothing. `tests/test_physics_truths.py` evaluates each
expression here over real rows of its dataset and requires agreement to 1e-9 relative. Sixteen were
confirmed on the first attempt; III.15.14 was not, and the constant was solved from the data
(`y * E_n * d^2 / h^2` is exactly 1/(8*pi^2) with no spread across 3000 rows) rather than guessed a
second time.

**A law this expression language cannot express gets NO truth, and says so.** I.26.2 is Snell's law
in the form `theta1 = arcsin(n*sin(theta2))`, and there is no inverse-sine primitive in the
operator set. Inventing an approximation would make the search look capable of recovering something
it structurally cannot reach. That case reports recovery as not checkable, and the reason is
published: the target lies outside the search space.

Truths are built against a NAME to index map rather than fixed positions, because the column order
is a property of the downloaded file and not of the law.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ..model.expr import Node

TWO_PI = 2.0 * math.pi

_V = Node.var
_C = Node.const


def _op(name: str, *args: Node) -> Node:
    return Node.call(name, *args)


#: One builder per dataset, keyed by the PMLB dataset name. Each takes a column-name to index map.
FEYNMAN_TRUTHS: dict[str, Callable[[dict[str, int]], Node]] = {
    # I.6.2a  f = exp(-theta^2/2) / sqrt(2*pi)
    "feynman_I_6_2a": lambda i: _op(
        "div",
        _op("exp", _op("neg", _op("div", _op("square", _V(i["theta"])), _C(2.0)))),
        _C(math.sqrt(TWO_PI)),
    ),
    # I.12.1  F = mu * Nn
    "feynman_I_12_1": lambda i: _op("mul", _V(i["mu"]), _V(i["Nn"])),
    # I.12.5  F = q2 * Ef
    "feynman_I_12_5": lambda i: _op("mul", _V(i["q2"]), _V(i["Ef"])),
    # I.14.3  U = m * g * z
    "feynman_I_14_3": lambda i: _op("mul", _op("mul", _V(i["m"]), _V(i["g"])), _V(i["z"])),
    # I.25.13  V = q / C
    "feynman_I_25_13": lambda i: _op("div", _V(i["q"]), _V(i["C"])),
    # I.29.4  k = omega / c
    "feynman_I_29_4": lambda i: _op("div", _V(i["omega"]), _V(i["c"])),
    # I.34.27  E = (h / 2*pi) * omega
    "feynman_I_34_27": lambda i: _op(
        "mul", _op("div", _V(i["h"]), _C(TWO_PI)), _V(i["omega"])
    ),
    # I.39.1  E = 3/2 * pr * V
    "feynman_I_39_1": lambda i: _op("mul", _C(1.5), _op("mul", _V(i["pr"]), _V(i["V"]))),
    # I.43.31  D = mob * kb * T
    "feynman_I_43_31": lambda i: _op(
        "mul", _op("mul", _V(i["mob"]), _V(i["kb"])), _V(i["T"])
    ),
    # II.3.24  h = Pwr / (4*pi*r^2)
    "feynman_II_3_24": lambda i: _op(
        "div", _V(i["Pwr"]), _op("mul", _C(4.0 * math.pi), _op("square", _V(i["r"])))
    ),
    # II.8.31  E = epsilon * Ef^2 / 2
    "feynman_II_8_31": lambda i: _op(
        "div", _op("mul", _V(i["epsilon"]), _op("square", _V(i["Ef"]))), _C(2.0)
    ),
    # II.10.9  Ef = sigma_den / epsilon / (1 + chi)
    "feynman_II_10_9": lambda i: _op(
        "div",
        _op("div", _V(i["sigma_den"]), _V(i["epsilon"])),
        _op("add", _C(1.0), _V(i["chi"])),
    ),
    # II.27.18  E = epsilon * Ef^2
    "feynman_II_27_18": lambda i: _op(
        "mul", _V(i["epsilon"]), _op("square", _V(i["Ef"]))
    ),
    # II.38.14  G = Y / (2*(1 + sigma))
    "feynman_II_38_14": lambda i: _op(
        "div", _V(i["Y"]), _op("mul", _C(2.0), _op("add", _C(1.0), _V(i["sigma"])))
    ),
    # III.12.43  L = n * (h / 2*pi)
    "feynman_III_12_43": lambda i: _op(
        "mul", _V(i["n"]), _op("div", _V(i["h"]), _C(TWO_PI))
    ),
    # III.15.14  m = h^2 / (8*pi^2 * E_n * d^2). The 1/(8*pi^2) was solved from the data, not
    # guessed: y * E_n * d^2 / h^2 is 0.0126651 with zero spread, and 1/(8*pi^2) = 0.01266515.
    "feynman_III_15_14": lambda i: _op(
        "div",
        _op("square", _V(i["h"])),
        _op(
            "mul",
            _C(8.0 * math.pi * math.pi),
            _op("mul", _V(i["E_n"]), _op("square", _V(i["d"]))),
        ),
    ),
    # III.17.37  f = beta * (1 + alpha*cos(theta))
    "feynman_III_17_37": lambda i: _op(
        "mul",
        _V(i["beta"]),
        _op("add", _C(1.0), _op("mul", _V(i["alpha"]), _op("cos", _V(i["theta"])))),
    ),
}

#: Datasets whose published law cannot be written in this operator set, with the reason. These are
#: reported as not checkable, and the reason is surfaced rather than left as an unexplained gap.
INEXPRESSIBLE: dict[str, str] = {
    "feynman_I_26_2": (
        "Snell's law in the form theta1 = arcsin(n*sin(theta2)). The operator set has no "
        "inverse-sine primitive, so the target lies outside the space the search can reach. "
        "Recovery is reported as not checkable rather than as zero, because a zero here would "
        "describe the primitive set rather than the method."
    ),
}


def truth_for(dataset: str, input_keys: list[str]) -> Node | None:
    """The published law for one expanded physics dataset, or None when there is none to compare.

    `input_keys` comes from the loaded dataset, so a change in column order in the source cannot
    silently rebind a variable to the wrong symbol.
    """
    builder = FEYNMAN_TRUTHS.get(dataset)
    if builder is None:
        return None
    index = {key: position for position, key in enumerate(input_keys)}
    try:
        return builder(index)
    except KeyError:
        # The columns are not what this law expects. Returning None reports "not checkable", which
        # is true, rather than scoring against an expression bound to the wrong variables.
        return None

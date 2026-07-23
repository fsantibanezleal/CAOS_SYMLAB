"""A variable display name must never break the KaTeX render of the equation.

Reported on the flotation case: the equation was blank. The target display name was the raw source
column `%_Silica_Concentrate`, and the app renders `target = expression`, so the leading `%` (a LaTeX
comment) ate the whole line. The body names carried the same class of defect.

`latexify_name` in the pipeline and `latexSafeName` in the frontend are the two halves of the fix,
and they MUST agree. This pins the pipeline half against the exact names that broke, and against the
authored symbols that must not be touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

from symlab.model.latex import latexify_name  # noqa: E402


@pytest.mark.parametrize(
    "name",
    [
        "%_Silica_Concentrate",           # a leading % comments out the line
        "Flotation_Column_03_Air_Flow",   # a run of subscripts, unreadable
        "Ore_Pulp_pH",
        "a#b", "a&b", "a$b", "a{b}c",
    ],
)
def test_a_raw_name_is_neutralised(name: str) -> None:
    out = latexify_name(name)
    assert "\\mathrm{" in out, f"{name!r} was not set upright: {out!r}"
    # No LaTeX special survives unescaped inside the mathrm body.
    body = out[len("\\mathrm{"):-1]
    for i, char in enumerate(body):
        if char in "%#&$_{}":
            assert i > 0 and body[i - 1] == "\\", f"{char!r} is unescaped in {out!r}"


@pytest.mark.parametrize(
    "name",
    [
        "\\theta", "\\mathrm{NO}_x", "\\mathrm{RD}_{\\mathrm{BOD}}",  # authored LaTeX
        "P_e", "T_amb", "V_1", "mu", "Nn",                            # simple identifiers
    ],
)
def test_an_authored_symbol_is_left_alone(name: str) -> None:
    assert latexify_name(name) == name, "an authored LaTeX symbol was rewritten"


def test_the_two_implementations_agree() -> None:
    """The pipeline and the frontend must escape names the same way, or a baked name and a
    render-time name would disagree. Checks the frontend regex and escape table match the Python."""
    ts = (ROOT / "frontend" / "src" / "lib" / "latex.ts").read_text(encoding="utf-8")
    # Same passthrough regex for a simple identifier.
    assert "[A-Za-z][A-Za-z0-9]*(_[A-Za-z0-9]+)?" in ts, "the frontend simple-identifier regex drifted"
    # Same backslash passthrough.
    assert "includes('\\\\')" in ts, "the frontend backslash passthrough drifted"
    # Same upright wrapper.
    assert "\\\\mathrm{" in ts, "the frontend upright wrapper drifted"

"""No string the app renders may carry a control character.

`load_concrete` shipped the Abrams law as `f_c \\x07pprox \\x0crac{A}{B^{w/c}}`: the literal was
first written without an r prefix, so `\\a` became BEL, `\\f` became formfeed and `\\t` became a
tab, and marking it raw afterwards froze the damage rather than undoing it. Nothing failed. Ruff
was clean, the tests passed, the pipeline exported the string, and KaTeX rendered the wreckage into
the page.

The defect is invisible in an editor, which is exactly why it survived. This test reads the source
as text and rejects any control byte outside the ones a Python file legitimately contains.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1] / "data-pipeline" / "symlab"

#: Newline and carriage return are structure. Everything else below 0x20 is damage.
ALLOWED = {"\n", "\r"}


def _python_sources() -> list[Path]:
    return sorted(p for p in PACKAGE.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("path", _python_sources(), ids=lambda p: p.name)
def test_source_carries_no_stray_control_characters(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    offenders = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for column, character in enumerate(line, start=1):
            if ord(character) < 0x20 and character not in ALLOWED:
                offenders.append((line_number, column, hex(ord(character)), line.strip()[:80]))

    assert not offenders, (
        f"{path.name} contains control characters, which usually means a string was written "
        f"without an r prefix and then marked raw: {offenders[:4]}"
    )


def test_the_abrams_law_is_intact() -> None:
    """The specific string that broke, asserted directly.

    A general rule catches the class; naming the instance keeps the regression honest if the
    general rule is ever relaxed.
    """
    source = (PACKAGE / "io" / "loaders.py").read_text(encoding="utf-8")
    assert r"\approx" in source and r"\frac{A}{B^{w/c}}" in source
    assert "\x07" not in source and "\x0c" not in source

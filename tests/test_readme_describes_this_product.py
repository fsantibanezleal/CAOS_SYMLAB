"""The README must describe THIS product.

It did not. The most visible file in a public repository opened with "This is the canonical template
every Faena/CAOS data-product repo is instantiated from", carried `<OWNER>/<REPO>` placeholders in
its badges, pointed at a `web/` directory this repo calls `frontend/`, and told the reader to replace
an EXAMPLE SIR engine that does not exist here.

`scripts/check_template_residue.py` passed on it throughout, because that guard looks for marker
files and known placeholder tokens rather than reading prose. So this test asserts the few things
that are cheap to check and would have caught it: no unresolved placeholders, the real repository
and product named, the real directory layout, and the claim the product is actually about.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

README = Path(__file__).resolve().parents[1] / "README.md"


@pytest.fixture(scope="module")
def text() -> str:
    return README.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "placeholder",
    ["<OWNER>", "<REPO>", "<SLUG>", "<slug>", "canonical template", "instantiate this template"],
)
def test_no_unresolved_template_placeholder(text: str, placeholder: str) -> None:
    assert placeholder not in text, (
        f"README still contains the template placeholder {placeholder!r}"
    )


def test_it_names_this_repository_and_product(text: str) -> None:
    assert "fsantibanezleal/CAOS_SYMLAB" in text, "the badges must point at this repository"
    assert "symlab.fasl-work.com" in text, "the README must link the live site"


def test_it_describes_the_real_directory_layout(text: str) -> None:
    """The template's quickstart pointed at `web/`; this repo's frontend is `frontend/`."""
    assert "cd frontend" in text
    assert not re.search(r"\bcd web\b", text), "the frontend directory is `frontend`, not `web`"


def test_it_states_the_claim_the_product_is_about(text: str) -> None:
    """A README that does not say what is being measured is a README for something else."""
    lowered = text.lower()
    assert "symbolic regression" in lowered
    assert "recovery" in lowered and "accuracy" in lowered, (
        "the README must state that accuracy and recovery are reported separately, which is the "
        "one claim this product exists to make"
    )
    assert "not checkable" in lowered, (
        "the README must say what happens on a case with no published law, because reporting it as "
        "zero recovery would be false"
    )


def test_every_relative_link_resolves(text: str) -> None:
    """A broken link in the front door is worse than a missing one: it looks maintained."""
    root = README.parent
    broken = []
    for target in re.findall(r"\]\((?!https?://|#)([^)]+)\)", text):
        path = (root / target.split("#", 1)[0]).resolve()
        if not path.exists():
            broken.append(target)
    assert not broken, f"README links that do not resolve: {broken}"

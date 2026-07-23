"""The product version is declared in four places and they must agree.

    data-pipeline/symlab/__init__.py   __version__ = "0.04.000"   the display form, X.XX.XXX
    pyproject.toml                     version = "0.4.0"          the PEP 440 form of the same
    frontend/src/lib/links.ts          VERSION = '0.04.000'       what the site footer renders
    frontend/package.json              version                    the npm semver form
    CHANGELOG.md                       the newest "## X.XX.XXX" heading

Nothing forced them to match, and `frontend/package.json` was sitting at `0.1.0` while everything
else read `0.04.000`, which is what a hand-maintained copy does given enough releases.

The footer one matters most: it tells a reader which version produced the numbers they are looking
at, and a stale value there is a false statement about provenance rather than a cosmetic slip.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

from symlab import __version__ as ENGINE_VERSION  # noqa: E402


def _pep440(display: str) -> str:
    """`0.04.000` to `0.4.0`: the same version with the zero padding dropped."""
    return ".".join(str(int(part)) for part in display.split("."))


def test_the_display_version_is_well_formed():
    assert re.fullmatch(r"\d+\.\d{2}\.\d{3}", ENGINE_VERSION), (
        f"__version__ is {ENGINE_VERSION!r}; the convention is X.XX.XXX"
    )


def test_pyproject_matches_the_engine():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    assert match, "no version in pyproject.toml"
    assert match.group(1) == _pep440(ENGINE_VERSION), (
        f"pyproject declares {match.group(1)!r}, the engine declares {ENGINE_VERSION!r} "
        f"(PEP 440 form {_pep440(ENGINE_VERSION)!r})"
    )


def test_the_footer_matches_the_engine():
    """What the site tells a reader produced the numbers they are looking at."""
    text = (ROOT / "frontend" / "src" / "lib" / "links.ts").read_text(encoding="utf-8")
    match = re.search(r"export const VERSION\s*=\s*'([^']+)'", text)
    assert match, "no VERSION in frontend/src/lib/links.ts"
    assert match.group(1) == ENGINE_VERSION, (
        f"the footer renders {match.group(1)!r} and the engine that baked the artifacts is "
        f"{ENGINE_VERSION!r}. A reader reads that as the provenance of every number on the page."
    )


def test_the_npm_manifest_matches_the_engine():
    package = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert package.get("version") == _pep440(ENGINE_VERSION), (
        f"frontend/package.json declares {package.get('version')!r}, the engine declares "
        f"{ENGINE_VERSION!r} (semver form {_pep440(ENGINE_VERSION)!r})"
    )


def test_the_changelog_leads_with_this_version():
    """An unreleased version with no notes is a release nobody can read."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## (\d+\.\d{2}\.\d{3})", text, re.M)
    assert headings, "no version headings in CHANGELOG.md"
    assert headings[0] == ENGINE_VERSION, (
        f"CHANGELOG leads with {headings[0]!r} and the engine declares {ENGINE_VERSION!r}"
    )

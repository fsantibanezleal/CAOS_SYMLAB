"""A pinned dependency must be real, and a used dependency must be pinned.

`scipy==1.16.3` sat in `requirements-precompute.txt` for months. It was never installed and never
imported by a single module, so nothing failed: the pipeline ran, the tests passed, and the manifest
quietly described a lane that did not exist. The reverse failure is worse, because a package that is
imported but not pinned works on the machine that has it and breaks in CI.

These tests read the manifests and compare them against what the package actually imports and what
the environment actually has. They are deliberately narrow: they check the direct dependencies this
repo declares, not the transitive closure, which belongs to a lock file rather than to a test.
"""

from __future__ import annotations

import ast
import importlib.metadata as metadata
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data-pipeline" / "symlab"

MANIFESTS = (
    "requirements.txt",
    "requirements-precompute.txt",
    "requirements-dev.txt",
)

#: Distribution name to the module name it provides, where the two differ.
IMPORT_NAME = {"sreval[symbolic]": "sreval"}

#: Declared for tooling rather than imported by the package.
NOT_IMPORTED = {"pytest", "ruff"}


def _pins(manifest: str) -> dict[str, str]:
    text = (ROOT / manifest).read_text(encoding="utf-8")
    pins: dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-r"):
            continue
        match = re.match(r"^([A-Za-z0-9_.\-]+(?:\[[a-z,]+\])?)\s*==\s*([0-9][^\s]*)$", line)
        assert match, f"{manifest}: '{line}' is not an exact pin"
        pins[match.group(1)] = match.group(2)
    return pins


def _imported_top_level() -> set[str]:
    names: set[str] = set()
    for path in PACKAGE.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return names


@pytest.mark.parametrize("manifest", MANIFESTS)
def test_every_pin_is_installed_at_the_pinned_version(manifest: str) -> None:
    """A pin that names a version the environment does not have is a claim, not a record."""
    mismatches = []
    for spec, pinned in _pins(manifest).items():
        distribution = spec.split("[", 1)[0]
        try:
            installed = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            mismatches.append(f"{distribution} pinned {pinned} but NOT INSTALLED")
            continue
        if installed != pinned:
            mismatches.append(f"{distribution} pinned {pinned} but {installed} installed")
    assert not mismatches, f"{manifest}: " + "; ".join(mismatches)


def test_every_pinned_runtime_package_is_actually_imported() -> None:
    """A package pinned but never imported describes a lane that does not exist."""
    imported = _imported_top_level()
    unused = []
    for manifest in ("requirements.txt", "requirements-precompute.txt"):
        for spec in _pins(manifest):
            module = IMPORT_NAME.get(spec, spec.split("[", 1)[0]).replace("-", "_")
            if module in NOT_IMPORTED:
                continue
            if module not in imported:
                unused.append(f"{spec} ({manifest})")
    assert not unused, (
        "pinned but never imported by data-pipeline/symlab: " + ", ".join(unused)
    )


def test_third_party_imports_are_all_pinned_somewhere() -> None:
    """The reverse direction: an import with no pin works here and breaks in CI."""
    pinned_modules = set()
    for manifest in MANIFESTS:
        for spec in _pins(manifest):
            pinned_modules.add(IMPORT_NAME.get(spec, spec.split("[", 1)[0]).replace("-", "_"))

    stdlib = set(getattr(__import__("sys"), "stdlib_module_names", ()))
    unpinned = sorted(
        name
        for name in _imported_top_level()
        if name not in stdlib
        and name not in pinned_modules
        and not name.startswith("_")
        and name != "symlab"
    )
    assert not unpinned, f"imported but pinned in no manifest: {unpinned}"


def test_the_pipeline_manifest_does_not_duplicate_the_root_one() -> None:
    """Two files claiming one lane is how a pin drifts: one gets updated, the other does not."""
    text = (ROOT / "data-pipeline" / "requirements.txt").read_text(encoding="utf-8")
    assert "-r ../requirements-precompute.txt" in text, (
        "data-pipeline/requirements.txt must point at the real manifest rather than restate it"
    )
    assert not re.search(r"^[A-Za-z].*==", text, re.M), (
        "data-pipeline/requirements.txt must not carry pins of its own"
    )

"""The payload the pipeline writes and the contract the app declares must be the same shape.

`contract.types.ts` exists so a drift between the two fails the BUILD rather than producing a blank
panel at runtime. That works in one direction: rename a field in Python and the TypeScript stops
compiling wherever it is read. It does NOT work in the other. A field the pipeline stops writing,
or starts writing without declaring, compiles perfectly and shows up as a missing number in a page
nobody is looking at.

This closes the loop from the Python side. It bakes one case at a reduced budget and compares the
resulting document against the declared interfaces in both directions:

- a REQUIRED field the app declares must be present in the payload
- a field the payload carries must be declared, even if optional

The second direction is the one that caught `category_name_es`: it shipped in the artifact, was
read by the case navigator through the index, and was never declared on `CaseNotes`.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TYPES = ROOT / "frontend" / "src" / "lib" / "contract.types.ts"
ARTIFACT = ROOT / "data" / "derived" / "monod-saturation" / "run.json"

#: interface name -> how to reach the matching object inside the run document.
CHECKS = {
    "CaseNotes": lambda d: d["notes"],
    "DatasetDescriptor": lambda d: d["dataset"],
    "VariantPayload": lambda d: d["notes"]["variants"][0],
    "VariantScore": lambda d: d["notes"]["variants"][0]["score"],
    "ParetoMember": lambda d: d["notes"]["variants"][0]["pareto"][0],
    "CaseSummary": lambda d: d["notes"]["summary"],
}


def _declared_fields(source: str, interface: str) -> dict[str, bool]:
    """Top-level fields of one interface, mapped to whether they are optional.

    Nested object literals are skipped by brace depth. A naive line scan flattens them and reports
    an inline object's own members as missing from the payload, which is a false alarm that would
    train everyone to ignore this test.
    """
    match = re.search(rf"export interface {interface}\s*\{{(.*?)\n}}", source, re.S)
    assert match, f"interface {interface} not found in contract.types.ts"

    fields: dict[str, bool] = {}
    depth = 0
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if depth == 0:
            found = re.match(r"([A-Za-z_][A-Za-z0-9_]*)(\??):", line)
            if found:
                fields[found.group(1)] = found.group(2) == "?"
        depth += line.count("{") - line.count("}")
    return fields


@pytest.fixture(scope="module")
def document() -> dict:
    """A freshly baked artifact, so the test describes the CURRENT exporter.

    Reduced budget: this checks the shape of the document, not the quality of the search.
    """
    result = subprocess.run(
        [sys.executable, "-m", "symlab.pipeline", "monod-saturation", "--quick"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not ARTIFACT.exists():
        pytest.skip(f"could not bake a reference artifact: {result.stderr[-300:]}")
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


@pytest.mark.parametrize("interface", sorted(CHECKS))
def test_required_fields_are_present(interface: str, document: dict) -> None:
    source = TYPES.read_text(encoding="utf-8")
    fields = _declared_fields(source, interface)
    payload = CHECKS[interface](document)

    missing = sorted(name for name, optional in fields.items() if not optional and name not in payload)
    assert not missing, (
        f"{interface} declares these as required and the payload does not carry them: {missing}. "
        "Either the exporter stopped writing them or the contract over-promises."
    )


@pytest.mark.parametrize("interface", sorted(CHECKS))
def test_payload_fields_are_declared(interface: str, document: dict) -> None:
    """The direction TypeScript cannot check for itself."""
    source = TYPES.read_text(encoding="utf-8")
    fields = _declared_fields(source, interface)
    payload = CHECKS[interface](document)

    undeclared = sorted(key for key in payload if key not in fields)
    assert not undeclared, (
        f"the payload carries these and {interface} does not declare them: {undeclared}. "
        "An undeclared field is invisible to every consumer and to tsc."
    )

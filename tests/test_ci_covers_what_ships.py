"""CI must check the things that can break the deploy.

The frontend was built only by the Pages deploy workflow, which runs on `main`. A TypeScript error
therefore passed CI on a pull request and failed after the merge, which is the worst place to find
it: the branch is already integrated and the site is already broken.

Worse than not checking is checking on a different runtime. A CI job that builds on a Node major the
deploy does not use can be green while the deploy fails, which looks like a flake rather than the
real incompatibility it is.

These assertions are deliberately shallow. They read the workflow as text rather than parsing YAML,
because the point is to notice a step disappearing, not to validate GitHub's schema.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
CI = WORKFLOWS / "ci.yml"
DEPLOY = WORKFLOWS / "deploy-pages.yml"


@pytest.fixture(scope="module")
def ci() -> str:
    return CI.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "command",
    [
        "pytest",
        "ruff check",
        "check_template_residue.py",
        "check_content_standards.py",
        "check_artifacts.py",
    ],
)
def test_ci_runs_the_python_gates(ci: str, command: str) -> None:
    assert command in ci, f"CI no longer runs {command}"


def test_ci_builds_the_frontend(ci: str) -> None:
    """A type error must fail the pull request, not the deploy."""
    assert "npm ci" in ci, "CI does not install the frontend"
    assert "npm run build" in ci, "CI does not build the frontend, so tsc never runs on a PR"


def test_ci_stages_the_artifacts_before_building(ci: str) -> None:
    """`copy-data.mjs` fails when a browser-safe engine module is missing.

    That check is why the live lane cannot ship again with every module fetch 404ing, and it only
    runs if CI calls it.
    """
    assert "copy-data.mjs" in ci


def test_ci_and_deploy_build_on_the_same_node_major() -> None:
    """Green on one runtime and broken on another reads as a flake, not as an incompatibility."""
    if not DEPLOY.exists():
        pytest.skip("no deploy workflow to compare against")

    def majors(text: str) -> set[str]:
        return {m.group(1).split(".")[0] for m in re.finditer(r'node-version:\s*"?(\d+)', text)}

    ci_majors = majors(CI.read_text(encoding="utf-8"))
    deploy_majors = majors(DEPLOY.read_text(encoding="utf-8"))
    if not ci_majors or not deploy_majors:
        pytest.skip("a workflow does not pin a node version")

    assert ci_majors == deploy_majors, (
        f"CI builds the frontend on Node {sorted(ci_majors)} but the deploy ships from "
        f"Node {sorted(deploy_majors)}. A green CI would not mean a working deploy."
    )

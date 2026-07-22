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

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
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


def test_the_live_worker_does_not_keep_its_own_module_list() -> None:
    """One list of engine modules, owned by the build step that copies them.

    There were two: `copy-data.mjs` decided what to copy, and `search.worker.ts` decided what to
    fetch into Pyodide. Adding the non-evolutionary arm to the first and not the second produced a
    browser that served `sparse.py` with HTTP 200 and still raised
    `ModuleNotFoundError: No module named 'symlab.search.sparse'`. Nothing failed at build time, and
    the live lane looked wired because the file was genuinely there.

    The copier writes `engine/modules.json` from what it actually put on disk; the worker loads
    exactly that.
    """
    frontend = ROOT / "frontend"
    worker = (frontend / "src" / "live" / "search.worker.ts").read_text(encoding="utf-8")
    copier = (frontend / "copy-data.mjs").read_text(encoding="utf-8")

    assert "modules.json" in copier, "copy-data.mjs must emit the engine manifest"
    assert "modules.json" in worker, "the worker must read the engine manifest"
    assert "symlab/search/engine.py" not in worker, (
        "the worker names an engine module directly, which means a second list has come back. "
        "The copier is the only party that knows what exists on disk."
    )


def test_the_smoke_bake_is_sandboxed(ci: str) -> None:
    """A single-case bake in the working tree rewrites the whole index with that one case.

    CI runs a smoke bake ("regenerate one case") and then check_artifacts, which now has a coverage
    check. Baking monod-saturation into the checkout truncates manifests/index.json from 55 cases to
    1, and the coverage check then reports 54 artifacts absent from the index and exits 1. The job
    goes red for a reason unrelated to the change under test.

    So the smoke bake MUST redirect its output. This asserts that the pipeline invocation in CI
    carries SYMLAB_OUTPUT_DIR on the same line, which is the same rule the artifact-protection tests
    enforce for the test suite: a bake never writes the canonical tree.
    """
    bake_lines = [
        line for line in ci.splitlines()
        if "symlab.pipeline" in line and "python" in line
    ]
    assert bake_lines, "CI no longer runs a pipeline smoke bake"
    for line in bake_lines:
        assert "SYMLAB_OUTPUT_DIR" in line, (
            f"the CI bake `{line.strip()}` writes the checked-out tree. It must set "
            "SYMLAB_OUTPUT_DIR, or it truncates the committed index and the next step fails."
        )


def test_the_recovery_verdict_is_derived_in_one_place() -> None:
    """No component may re-implement `symbolic ?? numerical` by hand.

    The recovery verdict is the lab's central claim, and it was written out in four components. It is
    a helper now (`frontend/src/lib/recovery.ts`), and this keeps it that way: the raw rule must not
    reappear outside that file, or the next edit to one copy silently disagrees with the other three.
    """
    src = ROOT / "frontend" / "src"
    pattern = re.compile(r"symbolic\s*!==\s*null\s*\?")
    offenders = []
    for path in src.rglob("*.ts*"):
        if path.name == "recovery.ts":
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert not offenders, (
        f"the recovery rule is hand-written in {offenders}. Use isRecovered() from lib/recovery.ts, "
        "so the verdict is decided in one place."
    )

"""Validate CONTRACT 2 on disk (the pipeline -> web artifact contract): the index COVERS the derived tree; each
manifest exists; each artifact exists, is non-empty, and its byte size matches the manifest; the lane matches the
gate verdict. Stdlib only (runs in CI WITHOUT installing the package). Exit non-zero on any drift.

Used by scripts/smoke.* and by .github/workflows/ci.yml, the mechanical guard that a product can't regress to
serving artifacts that don't match their manifests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
# The manifests live at the repository root next to the pipeline that writes them, not inside the
# derived tree; the derived tree holds only the artifacts the web serves.
MANIFESTS = ROOT / "manifests"


def main() -> int:
    idx_path = MANIFESTS / "index.json"
    if not idx_path.exists():
        print(f"FAIL: missing {idx_path} (run scripts/precompute.sh first)")
        return 1
    index = json.loads(idx_path.read_text(encoding="utf-8"))
    errs: list[str] = []
    for entry in index.get("cases", []):
        mp = ROOT / entry["manifest_path"]
        if not mp.exists():
            errs.append(f"missing manifest: {mp}")
            continue
        m = json.loads(mp.read_text(encoding="utf-8"))
        art = DERIVED / m["artifact"]["path"]
        if not art.exists():
            errs.append(f"missing artifact: {art}")
            continue
        size = art.stat().st_size
        if size != m["artifact"]["bytes"]:
            errs.append(f"byte drift {art}: manifest={m['artifact']['bytes']} disk={size}")
        if size == 0:
            errs.append(f"empty artifact: {art}")
        if m.get("gate", {}).get("lane") not in (None, m.get("lane")):
            errs.append(f"lane/gate mismatch: {entry['case_id']}")
    # COVERAGE, not just consistency. Everything above walks the INDEX, so a truncated index makes
    # this script pass while most of the tree goes unchecked: it once printed "OK: 1 cases" with 24
    # baked artifacts on disk, because a --quick run had rewritten the index with a single entry.
    # Silent truncation reading as full coverage is exactly what this file exists to prevent.
    indexed = {entry["case_id"] for entry in index.get("cases", [])}
    on_disk = {path.parent.name for path in DERIVED.glob("*/run.json")}

    missing_from_index = sorted(on_disk - indexed)
    if missing_from_index:
        errs.append(
            f"{len(missing_from_index)} artifact(s) on disk are absent from the index and were "
            f"never checked: {missing_from_index[:6]}. Run scripts/rebuild_index.py"
        )

    missing_on_disk = sorted(indexed - on_disk)
    if missing_on_disk:
        errs.append(f"index references cases with no artifact: {missing_on_disk[:6]}")

    if errs:
        print("CONTRACT 2 DRIFT:")
        for e in errs:
            print("  -", e)
        return 1
    print(
        f"CONTRACT 2 OK: {len(indexed)} cases indexed, {len(on_disk)} artifacts on disk, "
        "manifests and artifacts consistent, index covers the tree."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

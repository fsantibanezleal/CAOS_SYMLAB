#!/usr/bin/env python3
"""Rebuild manifests/index.json from whatever cases are already baked.

The pipeline writes the index for the cases IT ran, so running one case at a time leaves an index
naming only the last one. This rebuilds the index from the manifests actually on disk, which is what
the app needs in order to show everything that has been baked so far. It runs no searches and
changes no artifact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

from symlab.cases.registry import (  # noqa: E402
    CATEGORIES,
    CATEGORIES_ES,
    coverage_summary,
    get_case,
)
from symlab.stages.export import build_index  # noqa: E402

MANIFESTS = ROOT / "manifests"


def main() -> int:
    entries = []
    for path in sorted(MANIFESTS.glob("*.json")):
        if path.name == "index.json":
            continue
        manifest = json.loads(path.read_text(encoding="utf-8"))
        artifact = ROOT / "data" / "derived" / manifest["artifact"]["path"]
        if not artifact.exists():
            print(f"  skipping {path.name}: artifact missing")
            continue
        # Display names come from the registry rather than the manifest, so an index can be
        # rebuilt for artifacts baked before these fields existed without re-running any search.
        try:
            case = get_case(manifest["case_id"])
            name_en, name_es = case.name_en, case.name_es
            ground_truth_known = case.ground_truth_known
            real_or_synthetic = case.real_or_synthetic
        except KeyError:
            # Expanded cases are not in the registry, so fall back to the ARTIFACT, which carries
            # every one of these fields. Falling back to "unknown" instead put those cases in a lane
            # the case navigator does not offer, which made them unreachable in the app while the
            # index still counted them as published.
            notes = json.loads(artifact.read_text(encoding="utf-8")).get("notes", {})
            name_en = notes.get("name_en") or manifest["case_id"]
            name_es = notes.get("name_es") or name_en
            ground_truth_known = bool(notes.get("ground_truth_known", False))
            real_or_synthetic = notes.get("real_or_synthetic") or "synthetic"

        entries.append({
            "case_id": manifest["case_id"],
            "category": manifest["category"],
            "category_name": CATEGORIES.get(manifest["category"], manifest["category"]),
            "category_name_es": CATEGORIES_ES.get(manifest["category"], manifest["category"]),
            "name_en": name_en,
            "name_es": name_es,
            "ground_truth_known": ground_truth_known,
            "real_or_synthetic": real_or_synthetic,
            "manifest_path": f"manifests/{path.name}",
            "artifact_path": manifest["artifact"]["path"],
            "bytes": manifest["artifact"]["bytes"],
            "n_variants": len(manifest.get("variants", [])),
            "summary": manifest.get("summary", {}),
        })

    index = build_index(entries, coverage_summary())
    (MANIFESTS / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    total = sum(e["bytes"] for e in entries) / 1024
    print(f"index rebuilt: {len(entries)} cases, {total:.0f} KB of artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

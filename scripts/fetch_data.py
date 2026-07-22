#!/usr/bin/env python3
"""Fetch the real datasets into the vault, pin them by SHA-256, and record what arrived.

Run from the repository root:

    python scripts/fetch_data.py             # everything not already present
    python scripts/fetch_data.py --only ccpp concrete
    python scripts/fetch_data.py --verify    # re-hash what is on disk, download nothing

Nothing fetched here is committed. The vault lives on the scratch volume; the repository receives
only compact derived artifacts, plus tiny contract-passing samples from the sources whose licence
permits redistribution.

Every download writes a sidecar `.provenance.json` next to the file, holding the URL, the fetch
date, the byte count, the SHA-256, the licence, the redistribution verdict and the citation. That
sidecar is what lets a later session prove which bytes produced a published number, which matters
here because one canonical source in this field is already dead and another has grown since its
paper was written.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "data-pipeline"))

from symlab.io.sources import SOURCES, Source, sha256_of  # noqa: E402

USER_AGENT = "CAOS_SYMLAB dataset fetcher (research use; contact via the repository)"
CHUNK = 1 << 20


def human(n: int | None) -> str:
    if n is None:
        return "unknown size"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return f"{n:.1f} GB"


def download(source: Source, *, timeout: int = 180, retries: int = 3) -> Path:
    """Stream a source to the vault, with retries and a progress line."""
    target = source.path
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")

    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(source.url, headers={"User-Agent": USER_AGENT})
            started = time.perf_counter()
            with urllib.request.urlopen(request, timeout=timeout) as response:
                declared = response.headers.get("Content-Length")
                total = int(declared) if declared else None
                written = 0
                with partial.open("wb") as handle:
                    while True:
                        block = response.read(CHUNK)
                        if not block:
                            break
                        handle.write(block)
                        written += len(block)
                        if total:
                            pct = 100.0 * written / total
                            print(f"\r    {source.id}: {human(written)} / {human(total)} ({pct:5.1f}%)",
                                  end="", flush=True)
                        else:
                            print(f"\r    {source.id}: {human(written)}", end="", flush=True)
            partial.replace(target)
            elapsed = time.perf_counter() - started
            print(f"\r    {source.id}: {human(written)} in {elapsed:.1f}s" + " " * 20)
            return target
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            print(f"\n    attempt {attempt}/{retries} failed: {error}")
            if partial.exists():
                partial.unlink()
            if attempt == retries:
                raise
            time.sleep(2 * attempt)
    raise RuntimeError("unreachable")


def unpack(source: Source, path: Path) -> list[str]:
    """Unpack an archive next to itself. Returns the member names."""
    if source.unpack != "zip":
        return []
    destination = path.parent / "unpacked"
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        archive.extractall(destination)
    return names


LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def reject_lfs_pointer(source: Source, path: Path) -> None:
    """Fail loudly when the download is a Git LFS pointer instead of the data.

    GitHub serves LFS pointers with HTTP 200, so a status-code check reports success and the caller
    happily writes a 132-byte text stub where a dataset should be. That happened here on the first
    run for all 33 PMLB files. The fix is to use the media host, and this guard makes the failure
    mode impossible to reintroduce silently.
    """
    with path.open("rb") as handle:
        head = handle.read(len(LFS_POINTER_PREFIX))
    if head == LFS_POINTER_PREFIX:
        raise RuntimeError(
            f"{source.id}: downloaded a Git LFS POINTER, not the data ({path.stat().st_size} bytes). "
            "Use the media.githubusercontent.com host for LFS-backed files."
        )


def write_provenance(source: Source, path: Path, digest: str, members: list[str]) -> None:
    record = {
        "id": source.id,
        "name": source.name,
        "url": source.url,
        "fetched_on": date.today().isoformat(),
        "bytes": path.stat().st_size,
        "sha256": digest,
        "licence": source.licence,
        "redistribution": source.redistribution,
        "may_commit_sample": source.may_commit_sample,
        "citation": source.citation,
        "defects": list(source.defects),
        "notes": source.notes,
        "unpacked_members": members,
    }
    (path.parent / "provenance.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


def process(source: Source, *, verify_only: bool, force: bool) -> dict:
    path = source.path
    present = path.exists()

    if verify_only:
        if not present:
            return {"id": source.id, "status": "missing"}
        digest = sha256_of(path)
        expected = source.sha256
        status = "ok" if (expected is None or digest == expected) else "SHA MISMATCH"
        return {"id": source.id, "status": status, "sha256": digest, "bytes": path.stat().st_size}

    if present and not force:
        digest = sha256_of(path)
        if source.sha256 and digest != source.sha256:
            return {"id": source.id, "status": "SHA MISMATCH", "sha256": digest}
        return {"id": source.id, "status": "cached", "sha256": digest, "bytes": path.stat().st_size}

    print(f"  fetching {source.id} ({human(source.approx_bytes)}) from {source.url}")
    download(source)
    reject_lfs_pointer(source, path)
    digest = sha256_of(path)
    if source.sha256 and digest != source.sha256:
        return {"id": source.id, "status": "SHA MISMATCH", "sha256": digest}
    members = unpack(source, path)
    write_provenance(source, path, digest, members)
    return {
        "id": source.id, "status": "fetched", "sha256": digest,
        "bytes": path.stat().st_size, "unpacked": len(members),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and pin the SymLab datasets.")
    parser.add_argument("--only", nargs="*", default=None, help="source ids to fetch")
    parser.add_argument("--skip", nargs="*", default=[], help="source ids to skip")
    parser.add_argument("--verify", action="store_true", help="re-hash what is on disk, fetch nothing")
    parser.add_argument("--force", action="store_true", help="re-download even if present")
    parser.add_argument("--prefix", default=None, help="fetch every source whose id starts with this")
    args = parser.parse_args()

    selected = list(SOURCES.values())
    if args.only:
        selected = [s for s in selected if s.id in set(args.only)]
    if args.prefix:
        selected = [s for s in selected if s.id.startswith(args.prefix)]
    selected = [s for s in selected if s.id not in set(args.skip)]

    print(f"SymLab data fetch: {len(selected)} source(s)")
    results = []
    failures = []
    for source in selected:
        try:
            result = process(source, verify_only=args.verify, force=args.force)
        except Exception as error:  # noqa: BLE001 - a failed source must not abort the rest
            result = {"id": source.id, "status": "FAILED", "error": str(error)}
            failures.append(source.id)
        results.append(result)
        print(f"  {result['status']:>13}  {result['id']}")

    print()
    by_status: dict[str, int] = {}
    for result in results:
        by_status[result["status"]] = by_status.get(result["status"], 0) + 1
    for status, count in sorted(by_status.items()):
        print(f"  {status:>13}: {count}")

    manifest = REPO_ROOT / "data" / "raw" / "fetch-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(
        {"generated_on": date.today().isoformat(), "results": results}, indent=2
    ), encoding="utf-8")
    print(f"\n  manifest -> {manifest}")

    if failures:
        print(f"\n  FAILED: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

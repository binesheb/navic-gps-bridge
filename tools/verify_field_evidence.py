#!/usr/bin/env python3
"""Verify a collected GNSS field-evidence bundle and its SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_bundle(bundle: Path) -> list[str]:
    """Return deterministic integrity failures for a field-evidence bundle."""
    failures: list[str] = []
    bundle = bundle.resolve()
    manifest_path = bundle / "EVIDENCE_MANIFEST.json"
    if not bundle.is_dir():
        return [f"bundle does not exist: {bundle}"]
    if not manifest_path.is_file():
        return ["missing EVIDENCE_MANIFEST.json"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid manifest: {exc}"]

    if manifest.get("schema") != 1:
        failures.append("unsupported manifest schema")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        failures.append("manifest files must be a non-empty list")
        return failures

    seen = set()
    for entry in files:
        if not isinstance(entry, dict):
            failures.append("manifest contains a non-object file entry")
            continue
        name = entry.get("name")
        expected_bytes = entry.get("bytes")
        expected_sha = entry.get("sha256")
        if not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."}:
            failures.append(f"invalid evidence filename: {name!r}")
            continue
        if name in seen:
            failures.append(f"duplicate evidence filename: {name}")
            continue
        seen.add(name)
        if not isinstance(expected_bytes, int) or expected_bytes < 0:
            failures.append(f"invalid byte count for {name}")
            continue
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            failures.append(f"invalid SHA-256 for {name}")
            continue
        try:
            int(expected_sha, 16)
        except ValueError:
            failures.append(f"invalid SHA-256 for {name}")
            continue

        path = bundle / name
        if not path.is_file():
            failures.append(f"missing evidence file: {name}")
            continue
        actual_bytes = path.stat().st_size
        if actual_bytes != expected_bytes:
            failures.append(f"byte count mismatch for {name}: {actual_bytes} != {expected_bytes}")
            continue
        actual_sha = sha256(path)
        if actual_sha != expected_sha.lower():
            failures.append(f"SHA-256 mismatch for {name}")

    return failures


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    failures = verify_bundle(args.bundle)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"PASS: verified evidence bundle in {args.bundle.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    manifest_path = bundle / "EVIDENCE_MANIFEST.json"
    if not bundle.is_dir():
        return fail(f"bundle does not exist: {bundle}")
    if not manifest_path.is_file():
        return fail("missing EVIDENCE_MANIFEST.json")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"invalid manifest: {exc}")

    if manifest.get("schema") != 1:
        return fail("unsupported manifest schema")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        return fail("manifest files must be a non-empty list")

    seen = set()
    for entry in files:
        if not isinstance(entry, dict):
            return fail("manifest contains a non-object file entry")
        name = entry.get("name")
        expected_bytes = entry.get("bytes")
        expected_sha = entry.get("sha256")
        if not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."}:
            return fail(f"invalid evidence filename: {name!r}")
        if name in seen:
            return fail(f"duplicate evidence filename: {name}")
        seen.add(name)
        if not isinstance(expected_bytes, int) or expected_bytes < 0:
            return fail(f"invalid byte count for {name}")
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            return fail(f"invalid SHA-256 for {name}")
        try:
            int(expected_sha, 16)
        except ValueError:
            return fail(f"invalid SHA-256 for {name}")

        path = bundle / name
        if not path.is_file():
            return fail(f"missing evidence file: {name}")
        actual_bytes = path.stat().st_size
        if actual_bytes != expected_bytes:
            return fail(f"byte count mismatch for {name}: {actual_bytes} != {expected_bytes}")
        actual_sha = sha256(path)
        if actual_sha != expected_sha.lower():
            return fail(f"SHA-256 mismatch for {name}")

    print(f"PASS: verified {len(files)} evidence file(s) in {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

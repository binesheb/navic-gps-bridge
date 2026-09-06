#!/usr/bin/env python3
"""Verify a field-evidence manifest against the files it describes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> int:
    print(json.dumps({"passed": False, "error": message}, indent=2))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    if not manifest_path.is_file():
        return fail(f"manifest does not exist: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return fail(f"invalid manifest: {exc}")

    if not isinstance(manifest, dict):
        return fail("manifest root must be an object")
    if manifest.get("schema") != 1:
        return fail("unsupported manifest schema")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        return fail("manifest files must be a non-empty array")

    seen = set()
    verified = []
    for entry in files:
        if not isinstance(entry, dict):
            return fail("manifest file entry must be an object")
        name = entry.get("name")
        expected_bytes = entry.get("bytes")
        expected_sha = entry.get("sha256")
        if not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."}:
            return fail("manifest file names must be simple filenames")
        if name == manifest_path.name:
            return fail("manifest must not list itself")
        if name in seen:
            return fail(f"duplicate manifest file: {name}")
        seen.add(name)
        if not isinstance(expected_bytes, int) or expected_bytes < 0:
            return fail(f"invalid byte count for {name}")
        if not isinstance(expected_sha, str) or not SHA256_RE.fullmatch(expected_sha):
            return fail(f"invalid SHA-256 digest for {name}")

        path = manifest_path.parent / name
        if not path.is_file():
            return fail(f"evidence file does not exist: {name}")
        actual_bytes = path.stat().st_size
        actual_sha = sha256(path)
        if actual_bytes != expected_bytes:
            return fail(f"byte count mismatch for {name}: expected {expected_bytes}, got {actual_bytes}")
        if actual_sha != expected_sha:
            return fail(f"SHA-256 mismatch for {name}")
        verified.append({"name": name, "bytes": actual_bytes, "sha256": actual_sha})

    result = {
        "passed": True,
        "schema": manifest["schema"],
        "files_verified": len(verified),
        "files": verified,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

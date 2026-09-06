#!/usr/bin/env python3
"""Validate a field-evidence bundle before it is used for qualification."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_FILES = {
    "nmea-verdict.json",
    "live.csv",
    "serial.log",
}
REQUIRED_IDENTITY = ("firmware_commit", "device", "receiver", "test_id")


def validate_manifest(manifest_path: Path) -> dict:
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        return {"passed": False, "error": f"manifest does not exist: {manifest_path}"}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"passed": False, "error": f"invalid manifest: {exc}"}

    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        return {"passed": False, "error": "unsupported manifest schema"}

    missing_identity = [key for key in REQUIRED_IDENTITY if not isinstance(manifest.get(key), str) or not manifest[key].strip()]
    if missing_identity:
        return {"passed": False, "error": "missing required test identity: " + ", ".join(missing_identity)}

    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        return {"passed": False, "error": "manifest files must be a non-empty array"}

    names = set()
    for entry in entries:
        if not isinstance(entry, dict):
            return {"passed": False, "error": "manifest file entry must be an object"}
        name = entry.get("name")
        digest = entry.get("sha256")
        if not isinstance(name, str) or Path(name).name != name or not name or name in {".", ".."}:
            return {"passed": False, "error": "manifest file names must be simple filenames"}
        if name in names:
            return {"passed": False, "error": f"duplicate manifest file: {name}"}
        names.add(name)
        if not isinstance(entry.get("bytes"), int) or entry["bytes"] < 0:
            return {"passed": False, "error": f"invalid byte count for {name}"}
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            return {"passed": False, "error": f"invalid SHA-256 digest for {name}"}
        if not (manifest_path.parent / name).is_file():
            return {"passed": False, "error": f"evidence file does not exist: {name}"}

    missing_files = sorted(REQUIRED_FILES - names)
    if missing_files:
        return {"passed": False, "error": "missing required evidence files: " + ", ".join(missing_files)}

    return {
        "passed": True,
        "schema": manifest["schema"],
        "identity_complete": True,
        "required_files_present": True,
        "files_declared": len(entries),
        "device": manifest["device"].strip(),
        "firmware_commit": manifest["firmware_commit"].strip(),
        "receiver": manifest["receiver"].strip(),
        "test_id": manifest["test_id"].strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="path to EVIDENCE_MANIFEST.json")
    args = parser.parse_args()
    result = validate_manifest(args.manifest)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

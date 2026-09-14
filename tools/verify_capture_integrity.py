#!/usr/bin/env python3
"""Verify the integrity binding recorded in CAPTURE.json."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_FILES = {"live.csv", "nmea.log", "nmea_timeline.log"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(run: Path) -> dict:
    run = run.resolve()
    meta_path = run / "CAPTURE.json"
    if meta_path.is_symlink() or not meta_path.is_file():
        raise ValueError("CAPTURE.json is missing or is a symlink")
    try:
        report = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid CAPTURE.json: {exc}") from exc
    if not isinstance(report, dict):
        raise ValueError("CAPTURE.json root must be an object")

    integrity = report.get("evidence_integrity")
    if not isinstance(integrity, dict) or integrity.get("schema") != 1:
        raise ValueError("missing or unsupported evidence_integrity schema")
    if integrity.get("hash_algorithm") != "SHA-256" or integrity.get("self_excluded") is not True:
        raise ValueError("unsupported evidence_integrity policy")

    entries = integrity.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("evidence_integrity.files must be a non-empty list")

    names = set()
    mismatches = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("invalid evidence_integrity entry")
        name = entry.get("name")
        if not isinstance(name, str) or not name or Path(name).name != name:
            raise ValueError("evidence filename must be a single path component")
        if name in names:
            raise ValueError(f"duplicate evidence entry: {name}")
        names.add(name)
        path = run / name
        if path.is_symlink() or not path.is_file():
            mismatches.append({"name": name, "reason": "missing_or_symlink"})
            continue
        actual_bytes = path.stat().st_size
        actual_hash = sha256(path)
        if entry.get("bytes") != actual_bytes or entry.get("sha256") != actual_hash:
            mismatches.append({"name": name, "reason": "hash_or_size_mismatch"})

    missing_required = sorted(REQUIRED_FILES - names)
    if missing_required:
        raise ValueError("integrity record omits required evidence: " + ", ".join(missing_required))

    status = "PASS" if not mismatches else "FAIL"
    return {
        "schema": 1,
        "status": status,
        "checked_files": len(entries),
        "mismatches": mismatches,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Capture evidence directory")
    args = parser.parse_args(argv)
    try:
        result = verify(args.run)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

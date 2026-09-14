#!/usr/bin/env python3
"""Bind CAPTURE.json to the raw evidence files produced by a capture."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

REQUIRED_FILES = ("live.csv", "nmea.log", "nmea_timeline.log")
OPTIONAL_FILES = ("CAPTURE_QUALITY.json", "HARDWARE_PREFLIGHT.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file(run: Path, name: str) -> Path:
    path = run / name
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"evidence file is missing or is a symlink: {name}")
    return path


def finalize(run: Path) -> dict:
    run = run.resolve()
    if not run.is_dir():
        raise ValueError(f"capture directory does not exist: {run}")
    meta_path = _safe_file(run, "CAPTURE.json")
    try:
        report = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid CAPTURE.json: {exc}") from exc
    if not isinstance(report, dict):
        raise ValueError("CAPTURE.json root must be an object")

    files = []
    for name in REQUIRED_FILES + OPTIONAL_FILES:
        path = run / name
        if not path.exists():
            if name in REQUIRED_FILES:
                raise ValueError(f"required evidence file does not exist: {name}")
            continue
        path = _safe_file(run, name)
        files.append({"name": name, "bytes": path.stat().st_size, "sha256": sha256(path)})

    report["evidence_integrity"] = {
        "schema": 1,
        "hash_algorithm": "SHA-256",
        "self_excluded": True,
        "files": files,
    }
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix="CAPTURE.", suffix=".tmp", dir=run)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, meta_path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Capture evidence directory")
    args = parser.parse_args(argv)
    try:
        report = finalize(args.run)
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(report["evidence_integrity"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

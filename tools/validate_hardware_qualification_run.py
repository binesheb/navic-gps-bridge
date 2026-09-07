#!/usr/bin/env python3
"""Validate the structure and identity of a physical qualification run."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MATRIX_IDS = tuple(f"H{i:02d}" for i in range(1, 15))
REQUIRED_METADATA = ("schema_version", "status", "test_id", "device", "board", "firmware_commit", "receiver", "started_at")
REQUIRED_FILES = (
    "RUN_METADATA.json",
    "FIELD_QUALIFICATION_RUN.md",
    "nmea-verdict.json",
    "live.csv",
    "serial.log",
    "EVIDENCE_MANIFEST.json",
    "recovery-qualification.json",
    "recovery-verification.json",
    "FIELD_QUALIFICATION.md",
    "FIELD_QUALIFICATION_RESULT.json",
)
ROW_RE = re.compile(r"^\|\s*(H\d{2})\s*\|.*?\|\s*(PASS|FAIL|NOT_RUN)\s*\|", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Hardware qualification run directory")
    return parser.parse_args()


def load_metadata(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid RUN_METADATA.json: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("RUN_METADATA.json must contain an object")
    return value


def validate_run(run_dir: Path) -> list[str]:
    errors: list[str] = []
    if not run_dir.is_dir():
        return [f"run directory does not exist: {run_dir}"]

    missing = [name for name in REQUIRED_FILES if not (run_dir / name).is_file()]
    errors.extend(f"missing required file: {name}" for name in missing)
    if missing:
        return errors

    try:
        metadata = load_metadata(run_dir / "RUN_METADATA.json")
    except ValueError as exc:
        return [str(exc)]

    for key in REQUIRED_METADATA:
        if key not in metadata or metadata[key] in (None, ""):
            errors.append(f"missing metadata field: {key}")

    if metadata.get("schema_version") != 1:
        errors.append("unsupported schema_version; expected 1")
    if metadata.get("status") not in {"NOT_STARTED", "IN_PROGRESS", "COMPLETE"}:
        errors.append("invalid run status")
    if metadata.get("status") == "COMPLETE":
        errors.append("run is already COMPLETE; create a new run for another physical qualification")
    if metadata.get("completed_at") is not None:
        errors.append("completed_at must be null until finalization")

    checklist = (run_dir / "FIELD_QUALIFICATION_RUN.md").read_text(encoding="utf-8")
    rows = {case_id: result for case_id, result in ROW_RE.findall(checklist)}
    missing_rows = [case_id for case_id in MATRIX_IDS if case_id not in rows]
    errors.extend(f"missing checklist row: {case_id}" for case_id in missing_rows)

    unexpected = sorted(set(rows) - set(MATRIX_IDS))
    errors.extend(f"unexpected checklist row: {case_id}" for case_id in unexpected)

    return errors


def main() -> int:
    args = parse_args()
    errors = validate_run(args.run.resolve())
    if errors:
        print("hardware qualification run preflight: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("hardware qualification run preflight: PASS")
    print("- run identity is structurally complete")
    print("- H01-H14 checklist rows are present")
    print("- run is not already finalized")
    print("- no physical test result has been inferred")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Finalize a physical hardware qualification run without inventing results.

The operator checklist is the source of truth for H01-H14. This tool only
changes a run from IN_PROGRESS to COMPLETE when every matrix row is explicitly
marked PASS and all required evidence files are present and non-empty. It also
records the completion timestamp in RUN_METADATA.json.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

MATRIX_IDS = tuple(f"H{i:02d}" for i in range(1, 15))
REQUIRED_FILES = (
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
    parser.add_argument("run", type=Path, help="Existing hardware qualification run directory")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{path.name} must contain a JSON object")
    return value


def parse_matrix_results(text: str) -> dict[str, str]:
    """Return the latest recognized result for each H01-H14 matrix row."""
    return {case_id: result for case_id, result in ROW_RE.findall(text)}


def main() -> int:
    args = parse_args()
    run_dir = args.run.resolve()
    metadata_path = run_dir / "RUN_METADATA.json"
    checklist_path = run_dir / "FIELD_QUALIFICATION_RUN.md"

    if not run_dir.is_dir():
        raise SystemExit(f"run directory does not exist: {run_dir}")
    metadata = load_json(metadata_path)
    if not checklist_path.is_file():
        raise SystemExit("missing FIELD_QUALIFICATION_RUN.md")
    if metadata.get("status") == "COMPLETE":
        raise SystemExit("run is already COMPLETE")

    rows = parse_matrix_results(checklist_path.read_text(encoding="utf-8"))
    missing_rows = [case_id for case_id in MATRIX_IDS if case_id not in rows]
    if missing_rows:
        raise SystemExit("missing matrix rows: " + ", ".join(missing_rows))
    non_pass = [case_id for case_id in MATRIX_IDS if rows[case_id] != "PASS"]
    if non_pass:
        raise SystemExit("cannot finalize; matrix cases are not PASS: " + ", ".join(non_pass))

    missing = [name for name in REQUIRED_FILES if not (run_dir / name).is_file()]
    if missing:
        raise SystemExit("missing required evidence files: " + ", ".join(missing))
    empty = [name for name in REQUIRED_FILES if (run_dir / name).stat().st_size == 0]
    if empty:
        raise SystemExit("required evidence files are empty: " + ", ".join(empty))

    result_path = run_dir / "FIELD_QUALIFICATION_RESULT.json"
    result = load_json(result_path)
    if result.get("passed") is not True:
        raise SystemExit("FIELD_QUALIFICATION_RESULT.json must contain passed=true")

    metadata["status"] = "COMPLETE"
    metadata["completed_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(f"hardware qualification run finalized: {run_dir}")
    print("matrix: H01-H14 PASS")
    print("evidence: present and non-empty")
    print("qualification result: passed=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

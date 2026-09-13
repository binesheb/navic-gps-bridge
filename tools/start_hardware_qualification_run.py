#!/usr/bin/env python3
"""Start an existing hardware qualification run without editing result data."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Existing hardware qualification run directory")
    return parser.parse_args()


def start_run(run_dir: Path) -> str:
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        raise SystemExit(f"run directory does not exist: {run_dir}")

    metadata_path = run_dir / "RUN_METADATA.json"
    checklist_path = run_dir / "FIELD_QUALIFICATION_RUN.md"
    if not metadata_path.is_file():
        raise SystemExit("missing RUN_METADATA.json")
    if not checklist_path.is_file():
        raise SystemExit("missing FIELD_QUALIFICATION_RUN.md")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid RUN_METADATA.json: {exc}") from exc
    if not isinstance(metadata, dict):
        raise SystemExit("RUN_METADATA.json must contain an object")
    if metadata.get("status") != "NOT_STARTED":
        raise SystemExit(f"run status must be NOT_STARTED; found {metadata.get('status')!r}")
    if metadata.get("started_at") is not None:
        raise SystemExit("run already has a started_at timestamp")
    if metadata.get("completed_at") is not None:
        raise SystemExit("completed run cannot be started")

    started_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata["status"] = "IN_PROGRESS"
    metadata["started_at"] = started_at
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    checklist = checklist_path.read_text(encoding="utf-8")
    marker = "- Overall result: `NOT_STARTED`"
    if marker not in checklist:
        raise SystemExit("checklist does not contain the expected NOT_STARTED disposition")
    checklist = checklist.replace(marker, "- Overall result: `IN_PROGRESS`", 1)
    checklist_path.write_text(checklist, encoding="utf-8")
    return started_at


def main() -> int:
    args = parse_args()
    started_at = start_run(args.run_dir)
    print(f"started hardware qualification run: {args.run_dir.resolve()}")
    print(f"started_at: {started_at}")
    print("physical-test lifecycle started; H01-H14 results remain NOT_RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Start a scaffolded hardware qualification run before physical testing.

The scaffold is deliberately created as NOT_STARTED. This command records the
actual physical test start time and transitions the run to IN_PROGRESS. It does
not create, modify, or infer any H01-H14 result.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="hardware qualification run directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = args.run.resolve()
    metadata_path = run_dir / "RUN_METADATA.json"
    checklist_path = run_dir / "FIELD_QUALIFICATION_RUN.md"

    if not run_dir.is_dir():
        raise SystemExit(f"run directory does not exist: {run_dir}")
    if not metadata_path.is_file():
        raise SystemExit("missing RUN_METADATA.json")
    if not checklist_path.is_file():
        raise SystemExit("missing FIELD_QUALIFICATION_RUN.md")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read RUN_METADATA.json: {exc}") from exc
    if not isinstance(metadata, dict):
        raise SystemExit("RUN_METADATA.json must contain a JSON object")

    status = metadata.get("status")
    if status != "NOT_STARTED":
        raise SystemExit(f"run must be NOT_STARTED before start; current status: {status!r}")

    if metadata.get("started_at") is not None:
        raise SystemExit("cannot start; NOT_STARTED run already contains a physical test start timestamp")
    if metadata.get("completed_at") is not None:
        raise SystemExit("cannot start; NOT_STARTED run already contains a completion timestamp")

    started = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata["status"] = "IN_PROGRESS"
    metadata["started_at"] = started
    metadata["completed_at"] = None
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(f"hardware qualification run started: {run_dir}")
    print(f"started_at: {started}")
    print("matrix results remain NOT_RUN until physical evidence is recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

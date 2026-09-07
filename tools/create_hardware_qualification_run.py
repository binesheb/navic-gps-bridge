#!/usr/bin/env python3
"""Create a reproducible on-device hardware qualification run scaffold.

This tool does not claim any test result. It creates a run directory containing
metadata, a matrix checklist, and the standard evidence filenames so operators
can execute the documented hardware qualification protocol without manually
recreating its structure.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

MATRIX = [
    ("H01", "Cold startup with receiver connected"),
    ("H02", "Startup with receiver silent"),
    ("H03", "Cable disconnect during valid stream"),
    ("H04", "Recovery cooldown"),
    ("H05", "Recovery after reconnect"),
    ("H06", "GPS compatibility output"),
    ("H07", "TCP streaming"),
    ("H08", "Four-client capacity"),
    ("H09", "Web diagnostics"),
    ("H10", "Runtime recovery policy update"),
    ("H11", "Geofence enter/exit"),
    ("H12", "Geofence GNSS no-fix"),
    ("H13", "Dateline geofence"),
    ("H14", "30-minute soak"),
]

EVIDENCE_FILES = (
    "nmea-verdict.json",
    "live.csv",
    "serial.log",
    "EVIDENCE_MANIFEST.json",
    "recovery-qualification.json",
    "recovery-verification.json",
    "FIELD_QUALIFICATION.md",
    "FIELD_QUALIFICATION_RESULT.json",
)

SAFE = re.compile(r"^[A-Za-z0-9._-]+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Run directory to create")
    parser.add_argument("--device", required=True)
    parser.add_argument("--receiver", required=True)
    parser.add_argument("--firmware-commit", required=True)
    parser.add_argument("--test-id", required=True)
    parser.add_argument("--board", default="ESP32-S3")
    parser.add_argument("--operator", default="")
    parser.add_argument("--receiver-firmware", default="")
    parser.add_argument("--antenna", default="")
    parser.add_argument("--uart-baud", type=int, default=9600)
    return parser.parse_args()


def validate_identifier(name: str, value: str) -> None:
    if not value or len(value) > 200 or not SAFE.fullmatch(value):
        raise SystemExit(f"invalid {name}: use only letters, digits, '.', '_' and '-'")


def main() -> int:
    args = parse_args()
    for name in ("device", "test-id", "firmware-commit"):
        validate_identifier(name, getattr(args, name.replace("-", "_")))

    if args.uart_baud <= 0:
        raise SystemExit("--uart-baud must be positive")

    run_dir = args.output.resolve()
    run_dir.mkdir(parents=True, exist_ok=False)

    started = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata = {
        "schema_version": 1,
        "status": "NOT_STARTED",
        "test_id": args.test_id,
        "device": args.device,
        "board": args.board,
        "firmware_commit": args.firmware_commit,
        "receiver": args.receiver,
        "receiver_firmware": args.receiver_firmware,
        "antenna": args.antenna,
        "uart_baud": args.uart_baud,
        "operator": args.operator,
        "started_at": started,
        "completed_at": None,
    }
    (run_dir / "RUN_METADATA.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Hardware Qualification Run",
        "",
        "> This checklist is a run record. `NOT_RUN` is the initial state; do not replace it with `PASS` without the required physical evidence.",
        "",
        f"- Test ID: `{args.test_id}`",
        f"- Device: `{args.device}`",
        f"- Firmware commit: `{args.firmware_commit}`",
        f"- Receiver: `{args.receiver}`",
        "",
        "## Matrix",
        "",
        "| ID | Scenario | Result | Evidence / notes |",
        "|---|---|---|---|",
    ]
    lines.extend(f"| {case_id} | {scenario} | NOT_RUN | |" for case_id, scenario in MATRIX)
    lines += [
        "",
        "## Required evidence files",
        "",
        *[f"- `{name}`" for name in EVIDENCE_FILES],
        "",
        "## Final disposition",
        "",
        "- Overall result: `NOT_STARTED`",
        "- Physical receiver validation is required; synthetic CI results must not be recorded as hardware passes.",
    ]
    (run_dir / "FIELD_QUALIFICATION_RUN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for name in EVIDENCE_FILES:
        path = run_dir / name
        if name.endswith(".json"):
            path.write_text("{}\n", encoding="utf-8")
        else:
            path.write_text("", encoding="utf-8")

    print(f"created hardware qualification run: {run_dir}")
    print(f"test id: {args.test_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

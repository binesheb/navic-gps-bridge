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
import math
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
    "FIELD_ACCEPTANCE.json",
    "FIELD_QUALIFICATION.md",
    "FIELD_QUALIFICATION_RESULT.json",
)

# Files whose bytes are stable physical evidence and therefore belong in the
# manifest. The manifest itself and derived qualification records are validated
# separately because they are produced or updated after evidence collection.
MANIFEST_EVIDENCE_FILES = (
    "nmea-verdict.json",
    "live.csv",
    "serial.log",
    "recovery-qualification.json",
    "recovery-verification.json",
    "FIELD_ACCEPTANCE.json",
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
    parser.add_argument("--silence-limit-seconds", type=float, default=None)
    parser.add_argument("--recovery-cooldown-seconds", type=float, default=None)
    parser.add_argument("--geofence-center-lat", type=float, default=None)
    parser.add_argument("--geofence-center-lon", type=float, default=None)
    parser.add_argument("--geofence-radius-meters", type=float, default=None)
    return parser.parse_args()


def validate_identifier(name: str, value: str) -> None:
    if not value or len(value) > 200 or not SAFE.fullmatch(value):
        raise SystemExit(f"invalid {name}: use only letters, digits, '.', '_' and '-'")


def validate_metadata_text(name: str, value: str, *, required: bool = False) -> None:
    """Reject control characters so traceability fields remain line-safe and auditable."""
    if required and not value:
        raise SystemExit(f"{name} must not be empty")
    if len(value) > 200 or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise SystemExit(f"invalid {name}: must be at most 200 characters with no control characters")


def validate_optional_positive(name: str, value: float | None) -> None:
    if value is not None and (not math.isfinite(value) or value <= 0):
        raise SystemExit(f"{name} must be a finite positive number when provided")


def validate_geofence(args: argparse.Namespace) -> None:
    center_values = (args.geofence_center_lat, args.geofence_center_lon, args.geofence_radius_meters)
    supplied = [value is not None for value in center_values]
    if any(supplied) and not all(supplied):
        raise SystemExit("geofence center latitude, longitude, and radius must be provided together")
    if args.geofence_center_lat is not None and (
        not math.isfinite(args.geofence_center_lat) or not -90 <= args.geofence_center_lat <= 90
    ):
        raise SystemExit("--geofence-center-lat must be finite and between -90 and 90")
    if args.geofence_center_lon is not None and (
        not math.isfinite(args.geofence_center_lon) or not -180 <= args.geofence_center_lon <= 180
    ):
        raise SystemExit("--geofence-center-lon must be finite and between -180 and 180")
    validate_optional_positive("--geofence-radius-meters", args.geofence_radius_meters)


def main() -> int:
    args = parse_args()
    for name in ("device", "test-id", "firmware-commit"):
        validate_identifier(name, getattr(args, name.replace("-", "_")))

    for name in ("receiver", "board", "operator", "receiver-firmware", "antenna"):
        validate_metadata_text(name, getattr(args, name.replace("-", "_")))

    if args.uart_baud <= 0:
        raise SystemExit("--uart-baud must be positive")
    validate_optional_positive("--silence-limit-seconds", args.silence_limit_seconds)
    validate_optional_positive("--recovery-cooldown-seconds", args.recovery_cooldown_seconds)
    validate_geofence(args)

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
        "qualification_limits": {
            "silence_limit_seconds": args.silence_limit_seconds,
            "recovery_cooldown_seconds": args.recovery_cooldown_seconds,
        },
        "geofence": (
            {
                "center_lat": args.geofence_center_lat,
                "center_lon": args.geofence_center_lon,
                "radius_meters": args.geofence_radius_meters,
            }
            if args.geofence_center_lat is not None
            else None
        ),
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
        "## Entry-gate configuration",
        "",
        f"- Silence limit: `{args.silence_limit_seconds if args.silence_limit_seconds is not None else 'NOT_SET'}` seconds",
        f"- Recovery cooldown: `{args.recovery_cooldown_seconds if args.recovery_cooldown_seconds is not None else 'NOT_SET'}` seconds",
        f"- Geofence: `{args.geofence_center_lat}, {args.geofence_center_lon}` / `{args.geofence_radius_meters}` m" if args.geofence_center_lat is not None else "- Geofence: `NOT_SET`",
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
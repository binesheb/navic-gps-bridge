#!/usr/bin/env python3
"""Validate a simultaneous HTTP/NMEA field-capture evidence directory.

This is a preflight check for hardware qualification. It validates the capture
metadata and required artifacts without turning transport errors or reconnects
into a false hardware PASS.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_ARTIFACTS = ("CAPTURE.json", "live.csv", "nmea.log", "nmea_timeline.log")


def load_report(run: Path) -> dict:
    path = run / "CAPTURE.json"
    if not path.is_file():
        raise ValueError("CAPTURE.json is missing")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid CAPTURE.json: {exc}") from exc
    if not isinstance(report, dict):
        raise ValueError("CAPTURE.json must contain an object")
    return report


def validate_capture(run: Path) -> dict:
    run = run.resolve()
    if not run.is_dir():
        raise ValueError(f"capture directory does not exist: {run}")

    report = load_report(run)
    missing = [name for name in REQUIRED_ARTIFACTS if not (run / name).is_file()]
    if missing:
        raise ValueError("missing capture artifacts: " + ", ".join(missing))
    empty = [name for name in REQUIRED_ARTIFACTS if (run / name).stat().st_size == 0]
    if empty:
        raise ValueError("empty capture artifacts: " + ", ".join(empty))

    if report.get("schema_version") != 2:
        raise ValueError("unsupported CAPTURE.json schema_version; expected 2")
    if report.get("simultaneous_window") is not True:
        raise ValueError("capture is not marked as a simultaneous window")

    def positive_number(key: str) -> float:
        value = report.get(key)
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be a positive number") from exc
        if number <= 0:
            raise ValueError(f"{key} must be a positive number")
        return number

    positive_number("duration_s")
    positive_number("interval_s")

    for key in ("live_samples", "nmea_sentences", "nmea_connections", "nmea_timeline_records"):
        value = report.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{key} must be a positive integer")

    if report.get("nmea_port") not in range(1, 65536):
        raise ValueError("nmea_port must be between 1 and 65535")

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="capture evidence directory")
    args = parser.parse_args(argv)
    try:
        report = validate_capture(args.run)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps({"valid": True, "live_samples": report["live_samples"], "nmea_sentences": report["nmea_sentences"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

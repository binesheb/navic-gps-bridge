#!/usr/bin/env python3
"""Validate a simultaneous HTTP/NMEA field-capture evidence directory.

This is a preflight check for hardware qualification. It validates the capture
metadata and required artifacts without turning transport errors or reconnects
into a false hardware PASS.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


REQUIRED_ARTIFACTS = ("CAPTURE.json", "live.csv", "nmea.log", "nmea_timeline.log")


def load_report(run: Path) -> dict:
    path = run / "CAPTURE.json"
    if not path.is_file() or path.is_symlink():
        raise ValueError("CAPTURE.json must be a regular file")
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
    symlinked = [name for name in REQUIRED_ARTIFACTS if (run / name).is_symlink()]
    if symlinked:
        raise ValueError("capture artifacts must be regular files: " + ", ".join(symlinked))
    empty = [name for name in REQUIRED_ARTIFACTS if (run / name).stat().st_size == 0]
    if empty:
        raise ValueError("empty capture artifacts: " + ", ".join(empty))

    if report.get("schema_version") != 2:
        raise ValueError("unsupported CAPTURE.json schema_version; expected 2")
    if report.get("simultaneous_window") is not True:
        raise ValueError("capture is not marked as a simultaneous window")
    if report.get("nmea_timeline") != "nmea_timeline.log":
        raise ValueError("nmea_timeline must reference nmea_timeline.log")

    def positive_number(key: str) -> float:
        value = report.get(key)
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be a positive finite number") from exc
        if not math.isfinite(number) or number <= 0:
            raise ValueError(f"{key} must be a positive finite number")
        return number

    positive_number("duration_s")
    positive_number("interval_s")

    for key in ("live_samples", "nmea_sentences", "nmea_connections", "nmea_timeline_records"):
        value = report.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{key} must be a positive integer")

    if report.get("nmea_port") not in range(1, 65536):
        raise ValueError("nmea_port must be between 1 and 65535")

    live_path = run / "live.csv"
    with live_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if not rows or not rows[0]:
        raise ValueError("live.csv must contain a header")
    live_rows = len(rows) - 1
    if live_rows != report["live_samples"]:
        raise ValueError(
            f"live_samples does not match live.csv rows: metadata={report['live_samples']}, file={live_rows}"
        )

    nmea_lines = [line for line in (run / "nmea.log").read_text(encoding="utf-8").splitlines() if line]
    nmea_sentences = sum(line.startswith("$") for line in nmea_lines)
    if nmea_sentences != report["nmea_sentences"]:
        raise ValueError(
            f"nmea_sentences does not match nmea.log: metadata={report['nmea_sentences']}, file={nmea_sentences}"
        )

    timeline_lines = [line for line in (run / "nmea_timeline.log").read_text(encoding="utf-8").splitlines() if line]
    if len(timeline_lines) != report["nmea_timeline_records"]:
        raise ValueError(
            "nmea_timeline_records does not match nmea_timeline.log: "
            f"metadata={report['nmea_timeline_records']}, file={len(timeline_lines)}"
        )
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

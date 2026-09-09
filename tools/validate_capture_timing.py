#!/usr/bin/env python3
"""Validate elapsed-time continuity in a simultaneous field capture."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from validate_capture_integrity import validate_integrity


def _read_live_times(path: Path) -> list[float]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        values: list[float] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                values.append(float(row["elapsed_s"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"live.csv row {row_number} has invalid elapsed_s") from exc
        return values


def _read_timeline_times(path: Path) -> list[float]:
    values: list[float] = []
    for row_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split("\t", 3)
        if len(fields) != 4:
            raise ValueError(f"nmea_timeline.log row {row_number} must contain four tab-separated fields")
        try:
            values.append(float(fields[1]))
        except ValueError as exc:
            raise ValueError(f"nmea_timeline.log row {row_number} has invalid elapsed time") from exc
    return values


def _validate_sequence(name: str, values: list[float], duration: float) -> None:
    if not values:
        raise ValueError(f"{name} contains no timing records")
    previous = -1e-9
    for index, value in enumerate(values, start=1):
        if value < 0 or value > duration + 0.25:
            raise ValueError(f"{name} timing record {index} is outside capture duration")
        if value < previous:
            raise ValueError(f"{name} elapsed time is not monotonic")
        previous = value


def validate_timing(run: Path) -> dict:
    report = validate_integrity(run)
    duration = float(report["duration_s"])
    live = _read_live_times(run / "live.csv")
    timeline = _read_timeline_times(run / "nmea_timeline.log")
    _validate_sequence("live.csv", live, duration)
    _validate_sequence("nmea_timeline.log", timeline, duration)
    return {
        "valid": True,
        "duration_s": duration,
        "live_first_elapsed_s": live[0],
        "live_last_elapsed_s": live[-1],
        "timeline_first_elapsed_s": timeline[0],
        "timeline_last_elapsed_s": timeline[-1],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="capture evidence directory")
    args = parser.parse_args(argv)
    try:
        result = validate_timing(args.run.resolve())
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

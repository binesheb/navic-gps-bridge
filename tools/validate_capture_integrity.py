#!/usr/bin/env python3
"""Cross-check field-capture metadata against the captured evidence files."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from validate_field_capture import validate_capture

LIVE_FIELDS = ("elapsed_s", "timestamp", "fix", "latitude", "longitude", "altitude_m", "speed_kmh", "satellites", "health_state")


def _count_live(path: Path) -> int:
    try:
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != list(LIVE_FIELDS):
                raise ValueError("live.csv header does not match capture schema")
            return sum(1 for _ in reader)
    except (OSError, csv.Error) as exc:
        raise ValueError(f"invalid live.csv: {exc}") from exc


def _count_nmea(path: Path) -> int:
    try:
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("$"))
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"invalid nmea.log: {exc}") from exc


def _count_timeline(path: Path) -> int:
    try:
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"invalid nmea_timeline.log: {exc}") from exc


def validate_integrity(run: Path) -> dict:
    report = validate_capture(run)
    checks = {
        "live_samples": (_count_live(run / "live.csv"), report["live_samples"]),
        "nmea_sentences": (_count_nmea(run / "nmea.log"), report["nmea_sentences"]),
        "nmea_timeline_records": (_count_timeline(run / "nmea_timeline.log"), report["nmea_timeline_records"]),
    }
    mismatches = [
        f"{key} does not match artifact: metadata={expected} actual={actual}"
        for key, (actual, expected) in checks.items()
        if actual != expected
    ]
    if mismatches:
        raise ValueError("; ".join(mismatches))
    return {"valid": True, "counts": {key: actual for key, (actual, _) in checks.items()}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="capture evidence directory")
    args = parser.parse_args(argv)
    try:
        result = validate_integrity(args.run.resolve())
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

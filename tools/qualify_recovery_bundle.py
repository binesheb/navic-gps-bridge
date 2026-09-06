#!/usr/bin/env python3
"""Validate and qualify a simultaneous GNSS recovery evidence bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

from qualify_recovery_capture import qualify


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_capture(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid CAPTURE.json: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("CAPTURE.json must contain an object")
    if data.get("schema_version") != 2:
        raise ValueError("CAPTURE.json schema_version must be 2")
    if data.get("simultaneous_window") is not True:
        raise ValueError("CAPTURE.json must mark simultaneous_window=true")
    timeline = data.get("nmea_timeline")
    if timeline != "nmea_timeline.log":
        raise ValueError("CAPTURE.json must reference nmea_timeline.log")
    duration = data.get("duration_s")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("CAPTURE.json duration_s must be a finite positive number")
    return data


def validate_bundle(bundle: Path, max_recovery_seconds=None, max_nmea_outage_seconds=None):
    capture_path = bundle / "CAPTURE.json"
    capture = load_capture(capture_path)
    live = bundle / "live.csv"
    timeline = bundle / capture["nmea_timeline"]
    if not live.is_file():
        raise ValueError("bundle is missing live.csv")
    if not timeline.is_file():
        raise ValueError("bundle is missing nmea_timeline.log")

    report = qualify(str(live), str(timeline), max_recovery_seconds, max_nmea_outage_seconds)
    report["capture_schema_version"] = capture["schema_version"]
    report["simultaneous_window"] = True
    report["capture_duration_s"] = capture["duration_s"]
    report["capture_http_errors"] = capture.get("http_errors", 0)
    report["capture_nmea_sentences"] = capture.get("nmea_sentences", 0)
    report["capture_nmea_reconnects"] = capture.get("nmea_reconnects", 0)
    report["bundle_integrity"] = True
    report["evidence_sha256"] = {
        "CAPTURE.json": sha256_file(capture_path),
        "live.csv": sha256_file(live),
        "nmea_timeline.log": sha256_file(timeline),
    }
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bundle_dir")
    p.add_argument("--max-recovery-seconds", type=float)
    p.add_argument("--max-nmea-outage-seconds", type=float)
    p.add_argument("--json-output")
    args = p.parse_args(argv)
    for name, value in (("max-recovery-seconds", args.max_recovery_seconds), ("max-nmea-outage-seconds", args.max_nmea_outage_seconds)):
        if value is not None and (not math.isfinite(value) or value < 0):
            p.error(f"{name} must be finite and >= 0")
    try:
        report = validate_bundle(Path(args.bundle_dir), args.max_recovery_seconds, args.max_nmea_outage_seconds)
    except (OSError, ValueError) as exc:
        p.error(str(exc))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        Path(args.json_output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["qualification_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

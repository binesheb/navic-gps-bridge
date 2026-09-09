#!/usr/bin/env python3
"""Apply objective quality thresholds to a simultaneous field capture.

This gate is deliberately separate from artifact integrity and timing checks:
it evaluates whether the observed capture quality is sufficient for downstream
qualification evidence without claiming physical GNSS performance.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from validate_field_capture import validate_capture


def evaluate(report: dict, *, max_http_errors: int, max_nmea_reconnects: int,
             min_live_rate: float, min_nmea_sentences: int) -> dict:
    duration = float(report["duration_s"])
    live_samples = int(report["live_samples"])
    nmea_sentences = int(report["nmea_sentences"])
    http_errors = int(report.get("http_errors", 0))
    reconnects = int(report.get("nmea_reconnects", 0))
    live_rate = live_samples / duration
    failures: list[str] = []
    if http_errors > max_http_errors:
        failures.append(f"http_errors {http_errors} > {max_http_errors}")
    if reconnects > max_nmea_reconnects:
        failures.append(f"nmea_reconnects {reconnects} > {max_nmea_reconnects}")
    if live_rate < min_live_rate:
        failures.append(f"live_rate_hz {live_rate:.6f} < {min_live_rate:.6f}")
    if nmea_sentences < min_nmea_sentences:
        failures.append(f"nmea_sentences {nmea_sentences} < {min_nmea_sentences}")
    return {
        "schema_version": 1,
        "passed": not failures,
        "duration_s": duration,
        "live_samples": live_samples,
        "live_rate_hz": live_rate,
        "nmea_sentences": nmea_sentences,
        "http_errors": http_errors,
        "nmea_reconnects": reconnects,
        "thresholds": {
            "max_http_errors": max_http_errors,
            "max_nmea_reconnects": max_nmea_reconnects,
            "min_live_rate_hz": min_live_rate,
            "min_nmea_sentences": min_nmea_sentences,
        },
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--max-http-errors", type=int, default=0)
    parser.add_argument("--max-nmea-reconnects", type=int, default=0)
    parser.add_argument("--min-live-rate-hz", type=float, default=0.5)
    parser.add_argument("--min-nmea-sentences", type=int, default=1)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)

    if args.max_http_errors < 0 or args.max_nmea_reconnects < 0 or args.min_nmea_sentences < 0:
        parser.error("count thresholds must be >= 0")
    if not math.isfinite(args.min_live_rate_hz) or args.min_live_rate_hz <= 0:
        parser.error("min-live-rate-hz must be a finite positive number")

    try:
        report = validate_capture(args.run)
    except ValueError as exc:
        parser.error(str(exc))
    result = evaluate(report, max_http_errors=args.max_http_errors,
                      max_nmea_reconnects=args.max_nmea_reconnects,
                      min_live_rate=args.min_live_rate_hz,
                      min_nmea_sentences=args.min_nmea_sentences)
    if args.json_output:
        args.json_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

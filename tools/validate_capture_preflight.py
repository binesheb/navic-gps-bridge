#!/usr/bin/env python3
"""Run the complete software-side field-capture preflight in one command.

This tool composes the existing structure, artifact-integrity, timing, and
quality validators. It never modifies the capture directory and does not claim
physical GNSS performance or H01-H14 qualification.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from validate_capture_integrity import validate_integrity
from validate_capture_quality import evaluate
from validate_capture_timing import validate_timing
from validate_field_capture import validate_capture


def _run_check(name: str, func) -> dict:
    try:
        result = func()
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        return {"name": name, "passed": False, "error": str(exc)}
    return {"name": name, "passed": True, "result": result}


def preflight(
    run: Path,
    *,
    max_http_errors: int,
    max_nmea_reconnects: int,
    min_live_rate: float,
    min_nmea_sentences: int,
) -> dict:
    checks = [
        _run_check("capture", lambda: validate_capture(run)),
        _run_check("integrity", lambda: validate_integrity(run)),
        _run_check("timing", lambda: validate_timing(run)),
    ]

    quality = None
    try:
        capture = validate_capture(run)
        quality = evaluate(
            capture,
            max_http_errors=max_http_errors,
            max_nmea_reconnects=max_nmea_reconnects,
            min_live_rate=min_live_rate,
            min_nmea_sentences=min_nmea_sentences,
        )
        checks.append({"name": "quality", "passed": quality["passed"], "result": quality})
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        checks.append({"name": "quality", "passed": False, "error": str(exc)})

    return {
        "schema_version": 1,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "thresholds": {
            "max_http_errors": max_http_errors,
            "max_nmea_reconnects": max_nmea_reconnects,
            "min_live_rate_hz": min_live_rate,
            "min_nmea_sentences": min_nmea_sentences,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="capture evidence directory")
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

    result = preflight(
        args.run.resolve(),
        max_http_errors=args.max_http_errors,
        max_nmea_reconnects=args.max_nmea_reconnects,
        min_live_rate=args.min_live_rate_hz,
        min_nmea_sentences=args.min_nmea_sentences,
    )
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.json_output:
        args.json_output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

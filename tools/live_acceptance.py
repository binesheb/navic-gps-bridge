#!/usr/bin/env python3
"""Run a complete NavIC GPS Bridge live acceptance capture and verdict.

This is the field-test entry point: capture /api/live telemetry, then run the
same deterministic analyzer used by CI-oriented validation. The CSV is kept
whether the verdict passes or fails so the evidence can be inspected later.
"""

import argparse
import sys

from analyze_live_capture import analyze
from live_capture import capture


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="Bridge URL, e.g. http://192.168.4.1")
    parser.add_argument("output", help="CSV evidence output path")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--duration", type=float, default=1800,
                        help="Capture duration in seconds (default: 1800)")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--min-http-success", type=float, default=95.0)
    parser.add_argument("--min-fresh", type=float, default=90.0)
    parser.add_argument("--max-recovery-attempts", type=int)
    parser.add_argument("--min-recovery-attempts", type=int,
                        help="Require at least this many observed recovery attempts")
    parser.add_argument("--max-stale-samples", type=int, default=60)
    parser.add_argument("--json-output",
                        help="Optional machine-readable JSON verdict path")
    args = parser.parse_args(argv)

    if args.interval <= 0 or args.timeout <= 0 or args.duration < 0:
        parser.error("interval and timeout must be > 0; duration must be >= 0")
    if not 0 <= args.min_http_success <= 100 or not 0 <= args.min_fresh <= 100:
        parser.error("percentage thresholds must be between 0 and 100")
    if args.max_recovery_attempts is not None and args.max_recovery_attempts < 0:
        parser.error("max-recovery-attempts must be >= 0")
    if args.min_recovery_attempts is not None and args.min_recovery_attempts < 0:
        parser.error("min-recovery-attempts must be >= 0")
    if (args.min_recovery_attempts is not None and args.max_recovery_attempts is not None
            and args.min_recovery_attempts > args.max_recovery_attempts):
        parser.error("min-recovery-attempts cannot exceed max-recovery-attempts")
    if args.max_stale_samples < 0:
        parser.error("max-stale-samples must be >= 0")

    try:
        samples, failures = capture(
            args.base_url, args.output, args.interval, args.duration,
            args.username, args.password, args.timeout,
        )
    except KeyboardInterrupt:
        print("Acceptance capture interrupted; partial CSV retained.", file=sys.stderr)
        return 130

    print(f"Captured {samples} samples with {failures} request failure(s) to {args.output}")
    if not samples:
        print("FAIL: no successful samples were captured")
        return 1

    verdict = analyze(
        args.output,
        args.min_http_success,
        args.min_fresh,
        args.max_recovery_attempts,
        args.min_recovery_attempts,
        args.max_stale_samples,
        args.json_output,
    )
    return 1 if verdict else 0


if __name__ == "__main__":
    raise SystemExit(main())

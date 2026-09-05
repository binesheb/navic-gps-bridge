#!/usr/bin/env python3
"""Run the bridge's live HTTP and TCP NMEA checks as one field test.

The runner keeps the raw CSV/JSON evidence from each checker and writes one
combined JSON verdict. It intentionally does not claim physical recovery:
that remains an explicit, controlled test requirement handled by the health
sequence qualification tooling.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path


def _run(command: list[str]) -> tuple[int, str]:
    completed = subprocess.run(command, capture_output=True, text=True)
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode, output


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="Bridge URL, e.g. http://192.168.4.1")
    parser.add_argument("output_dir", help="Directory for raw captures and combined verdict")
    parser.add_argument("--duration", type=float, default=1800.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--nmea-port", type=int, default=10110)
    parser.add_argument("--min-http-success", type=float, default=95.0)
    parser.add_argument("--min-fresh", type=float, default=90.0)
    parser.add_argument("--max-stale-samples", type=int, default=60)
    parser.add_argument("--min-sentences", type=int, default=1)
    parser.add_argument("--min-valid-percent", type=float, default=100.0)
    parser.add_argument("--require-type", action="append", default=[])
    parser.add_argument("--min-recovery-attempts", type=int)
    parser.add_argument("--max-recovery-attempts", type=int)
    parser.add_argument("--username")
    parser.add_argument("--password")
    args = parser.parse_args(argv)

    for name, value in (("duration", args.duration), ("interval", args.interval),
                        ("min-http-success", args.min_http_success),
                        ("min-fresh", args.min_fresh),
                        ("min-valid-percent", args.min_valid_percent)):
        if not math.isfinite(value):
            parser.error(f"{name} must be finite")
    if args.duration <= 0 or args.interval <= 0:
        parser.error("duration and interval must be > 0")
    if not 0 <= args.min_http_success <= 100 or not 0 <= args.min_fresh <= 100:
        parser.error("HTTP/freshness thresholds must be between 0 and 100")
    if not 0 <= args.min_valid_percent <= 100:
        parser.error("min-valid-percent must be between 0 and 100")
    if args.nmea_port < 1 or args.nmea_port > 65535:
        parser.error("nmea-port must be between 1 and 65535")
    if args.min_sentences < 0 or args.max_stale_samples < 0:
        parser.error("minimum sentences and maximum stale samples must be >= 0")
    if args.min_recovery_attempts is not None and args.min_recovery_attempts < 0:
        parser.error("min-recovery-attempts must be >= 0")
    if args.max_recovery_attempts is not None and args.max_recovery_attempts < 0:
        parser.error("max-recovery-attempts must be >= 0")
    if (args.min_recovery_attempts is not None and args.max_recovery_attempts is not None
            and args.min_recovery_attempts > args.max_recovery_attempts):
        parser.error("min-recovery-attempts cannot exceed max-recovery-attempts")

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    live_csv = output / "live.csv"
    live_json = output / "live-verdict.json"
    nmea_json = output / "nmea-verdict.json"
    combined_json = output / "FIELD_ACCEPTANCE.json"

    live_command = [
        sys.executable, str(Path(__file__).with_name("live_acceptance.py")),
        args.base_url, str(live_csv), "--interval", str(args.interval),
        "--duration", str(args.duration),
        "--min-http-success", str(args.min_http_success),
        "--min-fresh", str(args.min_fresh),
        "--max-stale-samples", str(args.max_stale_samples),
        "--min-duration-s", str(args.duration),
        "--json-output", str(live_json),
    ]
    if args.username is not None:
        live_command += ["--username", args.username, "--password", args.password or ""]
    if args.min_recovery_attempts is not None:
        live_command += ["--min-recovery-attempts", str(args.min_recovery_attempts)]
    if args.max_recovery_attempts is not None:
        live_command += ["--max-recovery-attempts", str(args.max_recovery_attempts)]

    nmea_command = [
        sys.executable, str(Path(__file__).with_name("nmea_stream_check.py")),
        args.base_url.replace("http://", "").replace("https://", "").split("/", 1)[0].split(":", 1)[0],
        str(args.nmea_port), str(args.duration),
        "--min-sentences", str(args.min_sentences),
        "--min-valid-percent", str(args.min_valid_percent),
        "--min-duration-s", str(args.duration),
        "--json-output", str(nmea_json),
    ]
    for required in args.require_type:
        nmea_command += ["--require-type", required]

    # Run sequentially to keep laptop/bridge resource usage predictable. The
    # NMEA check starts after the HTTP capture, so both durations are explicit
    # evidence windows rather than pretending they were simultaneous.
    live_rc, live_output = _run(live_command)
    nmea_rc, nmea_output = _run(nmea_command)

    live_report = _load(live_json) if live_json.exists() else {"passed": False, "failures": ["missing live verdict"]}
    nmea_report = _load(nmea_json) if nmea_json.exists() else {"passed": False, "failures": ["missing NMEA verdict"]}
    combined = {
        "schema_version": 1,
        "base_url": args.base_url,
        "requested_duration_s": args.duration,
        "live": live_report,
        "nmea": nmea_report,
        "live_exit_code": live_rc,
        "nmea_exit_code": nmea_rc,
        "passed": bool(live_report.get("passed")) and bool(nmea_report.get("passed")),
        "physical_recovery_verified": False,
        "notes": [
            "HTTP and TCP NMEA checks use separate evidence windows.",
            "physical_recovery_verified remains false until a controlled recovery capture is qualified.",
        ],
    }
    with combined_json.open("w", encoding="utf-8") as stream:
        json.dump(combined, stream, indent=2, sort_keys=True)
        stream.write("\n")

    print(f"Combined field verdict: {'PASS' if combined['passed'] else 'FAIL'}")
    print(f"Evidence directory: {output}")
    print(f"Combined verdict: {combined_json}")
    if live_output:
        print(live_output)
    if nmea_output:
        print(nmea_output)
    return 0 if combined["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

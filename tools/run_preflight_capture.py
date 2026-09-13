#!/usr/bin/env python3
"""Run hardware-port preflight and capture evidence only after it passes."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port", help="Physical GNSS serial port, e.g. COM5 or /dev/ttyUSB0")
    parser.add_argument("base_url", help="Bridge HTTP(S) URL")
    parser.add_argument("output_dir", help="Evidence output directory")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--expect-vid")
    parser.add_argument("--expect-pid")
    parser.add_argument("--expect-serial-number")
    parser.add_argument("--expect-manufacturer")
    parser.add_argument("--expect-product")
    parser.add_argument("--expect-location")
    parser.add_argument("--expect-interface")
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--nmea-port", type=int, default=10110)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--reconnect-interval", type=float, default=1.0)
    parser.add_argument("--quality-gate", action="store_true")
    parser.add_argument("--max-http-errors", type=int, default=0)
    parser.add_argument("--max-nmea-reconnects", type=int, default=0)
    parser.add_argument("--min-live-rate-hz", type=float, default=0.5)
    parser.add_argument("--min-nmea-sentences", type=int, default=1)
    return parser.parse_args(argv)


def build_preflight_command(args, verdict_path: Path) -> list[str]:
    command = [sys.executable, "tools/hardware_port_preflight.py", args.port, "--baud", str(args.baud), "--json-output", str(verdict_path)]
    for option, value in (
        ("--expect-vid", args.expect_vid),
        ("--expect-pid", args.expect_pid),
        ("--expect-serial-number", args.expect_serial_number),
        ("--expect-manufacturer", args.expect_manufacturer),
        ("--expect-product", args.expect_product),
        ("--expect-location", args.expect_location),
        ("--expect-interface", args.expect_interface),
    ):
        if value is not None:
            command.extend([option, value])
    return command


def load_verdict(path: Path) -> dict:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"unable to read preflight verdict: {exc}") from exc
    if not isinstance(result, dict):
        raise RuntimeError("preflight verdict must be a JSON object")
    return result


def build_capture_command(args) -> list[str]:
    command = [sys.executable, "tools/capture_field_evidence.py", args.base_url, args.output_dir,
               "--duration", str(args.duration), "--interval", str(args.interval),
               "--nmea-port", str(args.nmea_port), "--timeout", str(args.timeout),
               "--reconnect-interval", str(args.reconnect_interval)]
    if args.quality_gate:
        command.append("--quality-gate")
    command.extend(["--max-http-errors", str(args.max_http_errors),
                    "--max-nmea-reconnects", str(args.max_nmea_reconnects),
                    "--min-live-rate-hz", str(args.min_live_rate_hz),
                    "--min-nmea-sentences", str(args.min_nmea_sentences)])
    return command


def main(argv=None) -> int:
    args = parse_args(argv)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    verdict_path = output / "HARDWARE_PREFLIGHT.json"

    preflight = subprocess.run(build_preflight_command(args, verdict_path), check=False)
    if preflight.returncode != 0:
        print("hardware preflight failed; capture was not started", file=sys.stderr)
        return preflight.returncode or 1

    try:
        verdict = load_verdict(verdict_path)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if verdict.get("passed") is not True:
        print("hardware preflight verdict is not an explicit pass; capture was not started", file=sys.stderr)
        return 1
    identity = verdict.get("identity")
    if not isinstance(identity, dict) or identity.get("device") != args.port:
        print("hardware preflight identity does not match requested port; capture was not started", file=sys.stderr)
        return 1

    capture = subprocess.run(build_capture_command(args), check=False)
    meta_path = output / "CAPTURE.json"
    if meta_path.exists():
        try:
            report = json.loads(meta_path.read_text(encoding="utf-8"))
            report["hardware_preflight"] = {
                "verdict_file": verdict_path.name,
                "passed": True,
                "port": args.port,
                "identity": identity,
            }
            meta_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except (OSError, json.JSONDecodeError, TypeError):
            return 1
    return capture.returncode


if __name__ == "__main__":
    raise SystemExit(main())

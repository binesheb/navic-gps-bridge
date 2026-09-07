#!/usr/bin/env python3
"""Capture raw NMEA from a GNSS receiver serial port for field evidence."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def checksum_ok(sentence: str) -> bool:
    if not sentence.startswith("$") or "*" not in sentence:
        return False
    body, supplied = sentence[1:].split("*", 1)
    if len(supplied) != 2:
        return False
    value = 0
    for char in body:
        value ^= ord(char)
    try:
        return value == int(supplied, 16)
    except ValueError:
        return False


def capture(port: str, baud: int, output: Path, seconds: float, timeout: float) -> dict:
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("pyserial is required; install requirements-field.txt") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    deadline = started + seconds
    total = valid = invalid = 0
    types: dict[str, int] = {}

    with serial.Serial(port=port, baudrate=baud, timeout=timeout) as stream, output.open("wb") as raw:
        while time.monotonic() < deadline:
            line = stream.readline()
            if not line:
                continue
            raw.write(line)
            raw.flush()
            text = line.decode("ascii", errors="replace").strip("\r\n")
            if not text.startswith("$"):
                continue
            total += 1
            if checksum_ok(text):
                valid += 1
                if len(text) >= 6:
                    formatter = text[1:6]
                    if formatter.isalnum():
                        types[formatter] = types.get(formatter, 0) + 1
            else:
                invalid += 1

    duration = time.monotonic() - started
    return {
        "schema": 1,
        "port": port,
        "baud": baud,
        "requested_duration_s": seconds,
        "duration_s": round(duration, 3),
        "sentences": total,
        "valid_sentences": valid,
        "invalid_sentences": invalid,
        "valid_percent": round(100.0 * valid / total, 3) if total else 0.0,
        "types": dict(sorted(types.items())),
        "output": str(output),
        "passed": total > 0 and valid == total and duration >= seconds,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port", help="serial device, e.g. COM5 or /dev/ttyUSB0")
    parser.add_argument("output", type=Path, help="raw NMEA capture path")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    if args.baud <= 0 or args.seconds <= 0 or args.timeout <= 0:
        parser.error("baud, seconds and timeout must be > 0")
    try:
        report = capture(args.port, args.baud, args.output, args.seconds, args.timeout)
    except (OSError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

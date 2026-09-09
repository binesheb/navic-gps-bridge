#!/usr/bin/env python3
"""Capture raw NMEA from a GNSS receiver serial port for field evidence."""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter
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


def sentence_kind(sentence: str) -> str | None:
    if len(sentence) < 6 or sentence[0] != "$":
        return None
    formatter = sentence[1:6]
    if len(formatter) != 5 or not formatter.isalnum():
        return None
    return formatter


def build_report(
    port: str,
    baud: int,
    requested_duration_s: float,
    duration_s: float,
    total: int,
    valid: int,
    invalid: int,
    types: Counter[str],
    min_sentences: int,
    min_valid_percent: float,
    required_types: list[str],
) -> dict:
    valid_percent = 100.0 * valid / total if total else 0.0
    failures: list[str] = []
    if total == 0:
        failures.append("FAIL: no NMEA sentences received")
    if total < min_sentences:
        failures.append(f"FAIL: received {total} sentence(s) < {min_sentences}")
    if total > 0 and valid_percent < min_valid_percent:
        failures.append(
            f"FAIL: valid NMEA percentage {valid_percent:.3f}% < {min_valid_percent:g}%"
        )
    if duration_s < requested_duration_s:
        failures.append(
            f"FAIL: capture duration {duration_s:.3f}s < {requested_duration_s:g}s"
        )
    missing_types = [kind for kind in required_types if types[kind] == 0]
    if missing_types:
        failures.append("FAIL: required sentence type(s) missing: " + ", ".join(missing_types))
    return {
        "schema": 2,
        "port": port,
        "baud": baud,
        "requested_duration_s": requested_duration_s,
        "duration_s": round(duration_s, 3),
        "sentences": total,
        "valid_sentences": valid,
        "invalid_sentences": invalid,
        "valid_percent": round(valid_percent, 3),
        "types": dict(sorted(types.items())),
        "min_sentences": min_sentences,
        "min_valid_percent": min_valid_percent,
        "required_types": required_types,
        "passed": not failures,
        "failures": failures,
    }


def capture(
    port: str,
    baud: int,
    output: Path,
    seconds: float,
    timeout: float,
    min_sentences: int,
    min_valid_percent: float,
    required_types: list[str],
) -> dict:
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("pyserial is required; install requirements-field.txt") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    deadline = started + seconds
    total = valid = invalid = 0
    types: Counter[str] = Counter()

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
                kind = sentence_kind(text)
                if kind:
                    types[kind] += 1
            else:
                invalid += 1

    duration = time.monotonic() - started
    return build_report(
        port,
        baud,
        seconds,
        duration,
        total,
        valid,
        invalid,
        types,
        min_sentences,
        min_valid_percent,
        required_types,
    )


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port", help="serial device, e.g. COM5 or /dev/ttyUSB0")
    parser.add_argument("output", type=Path, help="raw NMEA capture path")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--min-sentences", type=int, default=1,
                        help="Minimum total NMEA sentences required (default: 1)")
    parser.add_argument("--min-valid-percent", type=float, default=100.0,
                        help="Minimum checksum-valid sentence percentage (default: 100)")
    parser.add_argument("--require-type", action="append", default=[],
                        help="Require a sentence formatter such as GNRMC; repeatable")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)

    if args.baud <= 0 or args.seconds <= 0 or args.timeout <= 0:
        parser.error("baud, seconds and timeout must be > 0")
    if args.min_sentences < 0:
        parser.error("min-sentences must be >= 0")
    if not math.isfinite(args.min_valid_percent) or not 0.0 <= args.min_valid_percent <= 100.0:
        parser.error("min-valid-percent must be a finite value between 0 and 100")
    required_types = [value.upper() for value in args.require_type]
    if any(len(value) != 5 or not value.isalnum() for value in required_types):
        parser.error("require-type values must be five-character alphanumeric NMEA formatters")

    try:
        report = capture(
            args.port,
            args.baud,
            args.output,
            args.seconds,
            args.timeout,
            args.min_sentences,
            args.min_valid_percent,
            required_types,
        )
    except (OSError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    if args.json_output:
        write_report(args.json_output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    for failure in report["failures"]:
        print(failure)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

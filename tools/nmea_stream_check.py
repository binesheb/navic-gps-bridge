#!/usr/bin/env python3
"""Validate a live NMEA TCP stream from NavIC GPS Bridge.

Usage:
  python tools/nmea_stream_check.py HOST [PORT] [SECONDS]

The checker is dependency-free so it can be used on a laptop in front of a
field-test bridge. It validates NMEA checksums and can enforce minimum stream
quality, validity percentage, required sentence types, and capture duration.
Optional JSON output preserves a machine-readable field-test verdict.
"""

from __future__ import annotations

import argparse
import json
import socket
import time
from collections import Counter


def checksum_ok(sentence: str) -> bool:
    """Return True only when the complete NMEA checksum field is valid."""
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
    """Return the five-character NMEA formatter, e.g. GPRMC or GNGGA."""
    if len(sentence) < 6 or sentence[0] != "$":
        return None
    formatter = sentence[1:6]
    if len(formatter) != 5 or not formatter.isalnum():
        return None
    return formatter


def build_report(valid: int, invalid: int, counts: Counter[str],
                 talkers: Counter[str], duration: float,
                 min_sentences: int, min_valid_percent: float,
                 required_types: list[str], min_duration_s: float = 0.0) -> tuple[dict, list[str]]:
    total = valid + invalid
    valid_percent = 100.0 * valid / total if total else 0.0
    failures: list[str] = []
    if total == 0:
        failures.append("FAIL: no NMEA sentences received")
    if invalid:
        failures.append("FAIL: invalid NMEA checksum(s) detected")
    if total < min_sentences:
        failures.append(f"FAIL: received {total} sentence(s) < {min_sentences}")
    if total > 0 and valid_percent < min_valid_percent:
        failures.append(
            f"FAIL: valid NMEA percentage {valid_percent:.3f}% < {min_valid_percent:g}%"
        )
    if duration < min_duration_s:
        failures.append(
            f"FAIL: capture duration {duration:.3f}s < {min_duration_s:g}s"
        )
    missing_types = [kind for kind in required_types if counts[kind] == 0]
    if missing_types:
        failures.append("FAIL: required sentence type(s) missing: " + ", ".join(missing_types))

    report = {
        "duration_s": round(duration, 3),
        "sentences": total,
        "valid_sentences": valid,
        "invalid_sentences": invalid,
        "valid_percent": round(valid_percent, 3),
        "talkers": dict(talkers),
        "types": dict(counts),
        "min_sentences": min_sentences,
        "min_valid_percent": min_valid_percent,
        "min_duration_s": min_duration_s,
        "required_types": required_types,
        "passed": not failures,
        "failures": failures,
    }
    return report, failures


def write_report(path: str, report: dict) -> None:
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host")
    parser.add_argument("port", nargs="?", type=int, default=10110)
    parser.add_argument("seconds", nargs="?", type=float, default=30.0)
    parser.add_argument("--min-sentences", type=int, default=1,
                        help="Minimum total NMEA sentences required (default: 1)")
    parser.add_argument("--min-valid-percent", type=float, default=100.0,
                        help="Minimum checksum-valid sentence percentage (default: 100)")
    parser.add_argument("--min-duration-s", type=float,
                        help="Require actual stream capture duration to reach this many seconds")
    parser.add_argument("--require-type", action="append", default=[],
                        help="Require a sentence formatter such as GPRMC; repeatable")
    parser.add_argument("--json-output", help="Optional machine-readable JSON verdict path")
    args = parser.parse_args(argv)

    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    if args.seconds <= 0:
        parser.error("seconds must be > 0")
    if args.min_sentences < 0:
        parser.error("min-sentences must be >= 0")
    if not 0.0 <= args.min_valid_percent <= 100.0:
        parser.error("min-valid-percent must be between 0 and 100")
    if args.min_duration_s is not None and args.min_duration_s < 0:
        parser.error("min-duration-s must be >= 0")
    required_types = [value.upper() for value in args.require_type]
    if any(len(value) != 5 or not value.isalnum() for value in required_types):
        parser.error("require-type values must be five-character alphanumeric NMEA formatters")

    min_duration_s = args.seconds if args.min_duration_s is None else args.min_duration_s
    counts: Counter[str] = Counter()
    talkers: Counter[str] = Counter()
    valid = invalid = 0
    started = time.monotonic()
    deadline = started + args.seconds

    print(f"Connecting to {args.host}:{args.port} for {args.seconds:g}s...")
    try:
        with socket.create_connection((args.host, args.port), timeout=5) as sock:
            sock.settimeout(1.0)
            buffer = b""
            while time.monotonic() < deadline:
                try:
                    chunk = sock.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    raw, buffer = buffer.split(b"\n", 1)
                    sentence = raw.decode("ascii", errors="replace").strip("\r")
                    if not sentence:
                        continue
                    if checksum_ok(sentence):
                        valid += 1
                        kind = sentence_kind(sentence)
                        if kind:
                            counts[kind] += 1
                            talkers[kind[:2]] += 1
                    else:
                        invalid += 1
    except (OSError, ValueError) as exc:
        elapsed = time.monotonic() - started
        report = {
            "duration_s": round(elapsed, 3),
            "requested_duration_s": args.seconds,
            "sentences": valid + invalid,
            "valid_sentences": valid,
            "invalid_sentences": invalid,
            "valid_percent": round(100.0 * valid / (valid + invalid), 3) if valid + invalid else 0.0,
            "talkers": dict(talkers),
            "types": dict(counts),
            "min_sentences": args.min_sentences,
            "min_valid_percent": args.min_valid_percent,
            "min_duration_s": min_duration_s,
            "required_types": required_types,
            "passed": False,
            "failures": [f"FAIL: unable to connect/read NMEA stream: {exc}"],
        }
        if args.json_output:
            write_report(args.json_output, report)
        print(report["failures"][0])
        return 1

    elapsed = time.monotonic() - started
    report, failures = build_report(
        valid, invalid, counts, talkers, elapsed,
        args.min_sentences, args.min_valid_percent, required_types,
        min_duration_s,
    )
    report["requested_duration_s"] = args.seconds
    print(f"Sentences: {report['sentences']}  valid: {valid}  invalid: {invalid}")
    print(f"Duration: {elapsed:.3f}s (requested {args.seconds:g}s)")
    if talkers:
        print("Talkers:")
        for talker, count in talkers.most_common():
            print(f"  {talker}: {count}")
    if counts:
        print("Types:")
        for kind, count in counts.most_common():
            print(f"  {kind}: {count}")
    if failures:
        for failure in failures:
            print(failure)
    else:
        print("PASS: NMEA stream satisfies the requested checks")
    if args.json_output:
        write_report(args.json_output, report)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

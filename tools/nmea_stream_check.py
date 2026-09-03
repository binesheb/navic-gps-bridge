#!/usr/bin/env python3
"""Validate a live NMEA TCP stream from NavIC GPS Bridge.

Usage:
  python tools/nmea_stream_check.py HOST [PORT] [SECONDS]

The checker is intentionally dependency-free so it can be used on a laptop in
front of a field-test bridge. It validates NMEA checksums and reports sentence
counts, talker IDs, and invalid frames.
"""

from __future__ import annotations

import socket
import sys
import time
from collections import Counter


def checksum_ok(sentence: str) -> bool:
    if not sentence.startswith("$") or "*" not in sentence:
        return False
    body, supplied = sentence[1:].split("*", 1)
    supplied = supplied[:2]
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


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: nmea_stream_check.py HOST [PORT] [SECONDS]", file=sys.stderr)
        return 2

    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 10110
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0

    counts: Counter[str] = Counter()
    talkers: Counter[str] = Counter()
    valid = invalid = 0
    deadline = time.monotonic() + duration

    print(f"Connecting to {host}:{port} for {duration:g}s...")
    with socket.create_connection((host, port), timeout=5) as sock:
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

    total = valid + invalid
    print(f"Sentences: {total}  valid: {valid}  invalid: {invalid}")
    if talkers:
        print("Talkers:")
        for talker, count in talkers.most_common():
            print(f"  {talker}: {count}")
    if counts:
        print("Types:")
        for kind, count in counts.most_common():
            print(f"  {kind}: {count}")

    if total == 0:
        print("FAIL: no NMEA sentences received")
        return 1
    if invalid:
        print("FAIL: invalid NMEA checksum(s) detected")
        return 1
    print("PASS: NMEA stream received with valid checksums")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

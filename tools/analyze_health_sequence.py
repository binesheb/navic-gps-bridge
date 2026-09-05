#!/usr/bin/env python3
"""Analyze /api/live CSV captures for health-state transitions.

The analyzer is intentionally dependency-free and treats the CSV as field
 evidence. It validates elapsed-time ordering, reports observed states and
 transition timing, and only marks a capture qualification-ready when the
 expected recovery sequence is supported by structurally valid timestamps.
"""

import argparse
import csv
import json
import math
import sys

EXPECTED = ("HEALTHY", "STALE", "RECOVERING", "HEALTHY")


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "status" not in reader.fieldnames:
            raise ValueError("CSV must contain a status column")
        if "elapsed_s" not in reader.fieldnames:
            raise ValueError("CSV must contain an elapsed_s column")
        rows = []
        previous = None
        for line_number, row in enumerate(reader, start=2):
            raw_elapsed = (row.get("elapsed_s") or "").strip()
            if not raw_elapsed:
                raise ValueError(f"line {line_number}: elapsed_s is empty")
            try:
                elapsed = float(raw_elapsed)
            except ValueError as exc:
                raise ValueError(f"line {line_number}: invalid elapsed_s") from exc
            if not math.isfinite(elapsed):
                raise ValueError(f"line {line_number}: elapsed_s must be finite")
            if previous is not None and elapsed < previous:
                raise ValueError(f"line {line_number}: elapsed_s moved backwards")
            previous = elapsed
            rows.append({"status": (row.get("status") or "").strip(), "elapsed_s": elapsed})
        return rows


def compress(rows):
    result = []
    for row in rows:
        state = row["status"]
        if not state:
            continue
        if not result or result[-1]["status"] != state:
            result.append(row)
    return result


def find_recovery(transitions):
    pos = 0
    matched = []
    for row in transitions:
        if row["status"] == EXPECTED[pos]:
            matched.append(row)
            pos += 1
            if pos == len(EXPECTED):
                return matched
    return None


def analyze(path, max_recovery_seconds=None):
    rows = read_rows(path)
    transitions = compress(rows)
    counts = {}
    for row in rows:
        if row["status"]:
            counts[row["status"]] = counts.get(row["status"], 0) + 1

    matched = find_recovery(transitions)
    recovery_observed = matched is not None
    recovery_duration = None
    if recovery_observed:
        recovery_duration = matched[-1]["elapsed_s"] - matched[-2]["elapsed_s"]

    duration_ok = max_recovery_seconds is None or (
        recovery_duration is not None and recovery_duration <= max_recovery_seconds
    )
    integrity_valid = all(
        rows[index]["elapsed_s"] <= rows[index + 1]["elapsed_s"]
        for index in range(max(0, len(rows) - 1))
    )
    return {
        "samples": len(rows),
        "non_empty_samples": sum(bool(row["status"]) for row in rows),
        "states": counts,
        "transitions": [row["status"] for row in transitions],
        "recovery_sequence": list(EXPECTED),
        "recovery_sequence_observed": recovery_observed,
        "recovery_duration_s": recovery_duration,
        "max_recovery_seconds": max_recovery_seconds,
        "recovery_duration_within_limit": duration_ok,
        "capture_integrity_valid": integrity_valid,
        "qualification_ready": recovery_observed and duration_ok and integrity_valid,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--max-recovery-seconds", type=float)
    args = parser.parse_args(argv)
    if args.max_recovery_seconds is not None and not math.isfinite(args.max_recovery_seconds):
        parser.error("max-recovery-seconds must be finite")
    if args.max_recovery_seconds is not None and args.max_recovery_seconds < 0:
        parser.error("max-recovery-seconds must be >= 0")
    try:
        report = analyze(args.csv_path, args.max_recovery_seconds)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"samples: {report['samples']}")
        print(f"non_empty_samples: {report['non_empty_samples']}")
        print("states: " + ", ".join(f"{k}={v}" for k, v in sorted(report["states"].items())))
        print("transitions: " + " -> ".join(report["transitions"]))
        print(f"recovery_sequence_observed: {report['recovery_sequence_observed']}")
        print(f"recovery_duration_s: {report['recovery_duration_s']}")
        print(f"capture_integrity_valid: {report['capture_integrity_valid']}")
        print(f"qualification_ready: {report['qualification_ready']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

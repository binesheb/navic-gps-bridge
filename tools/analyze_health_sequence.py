#!/usr/bin/env python3
"""Analyze /api/live CSV captures for health-state transitions.

The analyzer is intentionally dependency-free and treats the CSV as field
 evidence: it reports observed states, transition counts, and whether a
 recovery sequence was actually observed. It does not infer hardware success
 from missing data.
"""

import argparse
import csv
import json
import sys

EXPECTED = ("HEALTHY", "STALE", "RECOVERING", "HEALTHY")


def read_statuses(path):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "status" not in reader.fieldnames:
            raise ValueError("CSV must contain a status column")
        return [row.get("status", "").strip() for row in reader]


def compress(states):
    result = []
    for state in states:
        if not state:
            continue
        if not result or result[-1] != state:
            result.append(state)
    return result


def contains_subsequence(states, expected):
    pos = 0
    for state in states:
        if state == expected[pos]:
            pos += 1
            if pos == len(expected):
                return True
    return False


def analyze(path):
    statuses = read_statuses(path)
    transitions = compress(statuses)
    counts = {}
    for state in statuses:
        if state:
            counts[state] = counts.get(state, 0) + 1
    recovery_observed = contains_subsequence(transitions, EXPECTED)
    return {
        "samples": len(statuses),
        "non_empty_samples": sum(bool(s) for s in statuses),
        "states": counts,
        "transitions": transitions,
        "recovery_sequence": list(EXPECTED),
        "recovery_sequence_observed": recovery_observed,
        "qualification_ready": recovery_observed,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        report = analyze(args.csv_path)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"samples: {report['samples']}")
        print(f"non_empty_samples: {report['non_empty_samples']}")
        print("states: " + ", ".join(f"{k}={v}" for k, v in sorted(report["states"].items())))
        print("transitions: " + " -> ".join(report["transitions"]) )
        print(f"recovery_sequence_observed: {report['recovery_sequence_observed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

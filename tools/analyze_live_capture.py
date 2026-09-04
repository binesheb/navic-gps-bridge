#!/usr/bin/env python3
"""Analyze a NavIC GPS Bridge /api/live capture CSV for repeatable validation."""

import argparse
import csv
import math


REQUIRED_FIELDS = {"http_ok", "data_available", "uptime_ms"}
BOOLEAN_FIELDS = ("http_ok", "data_available", "data_fresh")
NUMERIC_FIELDS = ("uptime_ms", "recovery_attempts")


def _float(row, key):
    value = row.get(key, "")
    if value in (None, ""):
        return None
    return float(value)


def _bool(row, key):
    value = row.get(key, "").strip().lower()
    if value in ("true", "1", "yes"):
        return True
    if value in ("false", "0", "no"):
        return False
    return None


def _max_consecutive_stale(rows):
    longest = current = 0
    for row in rows:
        fresh = _bool(row, "data_fresh")
        if fresh is False:
            current += 1
            longest = max(longest, current)
        elif fresh is True:
            current = 0
    return longest


def analyze(path, min_http_success=95.0, min_fresh=90.0, max_recovery_attempts=None, max_stale_samples=60):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        rows = list(reader)

    if not REQUIRED_FIELDS.issubset(fields):
        missing = ", ".join(sorted(REQUIRED_FIELDS - fields))
        return [f"FAIL: capture is missing required columns: {missing}"]

    if not rows:
        return ["FAIL: capture contains no samples"]

    failures = []
    for index, row in enumerate(rows, start=2):
        for key in BOOLEAN_FIELDS:
            if key in fields and row.get(key, "") not in (None, "") and _bool(row, key) is None:
                failures.append(f"FAIL: invalid {key} value on CSV line {index}")
        for key in NUMERIC_FIELDS:
            if key in fields and row.get(key, "") not in (None, ""):
                try:
                    value = _float(row, key)
                except ValueError:
                    failures.append(f"FAIL: invalid {key} value on CSV line {index}")
                    continue
                if value is not None and not math.isfinite(value):
                    failures.append(f"FAIL: non-finite {key} value on CSV line {index}")

    http_known = [r for r in rows if _bool(r, "http_ok") is not None]
    http_ok = sum(_bool(r, "http_ok") is True for r in http_known)
    http_rate = 100.0 * http_ok / len(http_known) if http_known else 0.0
    if http_rate < min_http_success:
        failures.append(f"FAIL: HTTP success {http_rate:.1f}% < {min_http_success:.1f}%")

    fresh_known = [r for r in rows if _bool(r, "data_fresh") is not None]
    fresh = sum(_bool(r, "data_fresh") is True for r in fresh_known)
    fresh_rate = 100.0 * fresh / len(fresh_known) if fresh_known else 0.0
    if "data_fresh" in fields and not fresh_known:
        failures.append("FAIL: capture contains no valid data_fresh samples")
    elif fresh_known and fresh_rate < min_fresh:
        failures.append(f"FAIL: fresh-data ratio {fresh_rate:.1f}% < {min_fresh:.1f}%")

    max_stale = _max_consecutive_stale(rows) if "data_fresh" in fields else 0
    if "data_fresh" in fields and max_stale > max_stale_samples:
        failures.append(
            f"FAIL: consecutive stale samples reached {max_stale} > {max_stale_samples}"
        )

    uptimes = []
    for row in rows:
        try:
            value = _float(row, "uptime_ms")
        except ValueError:
            continue
        if value is not None and math.isfinite(value):
            uptimes.append(value)
    if len(uptimes) >= 2 and any(b < a for a, b in zip(uptimes, uptimes[1:])):
        failures.append("FAIL: uptime_ms moved backwards; possible reboot/reset")

    recoveries = []
    for row in rows:
        try:
            value = _float(row, "recovery_attempts")
        except ValueError:
            continue
        if value is not None and math.isfinite(value):
            recoveries.append(value)
    max_recovery = max(recoveries) if recoveries else 0
    if max_recovery_attempts is not None and max_recovery > max_recovery_attempts:
        failures.append(
            f"FAIL: recovery attempts reached {int(max_recovery)} > {max_recovery_attempts}"
        )

    available = [_bool(r, "data_available") for r in rows]
    available = [v for v in available if v is not None]
    available_count = sum(available)

    print(f"Samples: {len(rows)}")
    print(f"HTTP success: {http_rate:.1f}%")
    if fresh_known:
        print(f"Fresh-data ratio: {fresh_rate:.1f}%")
        print(f"Maximum consecutive stale samples: {max_stale}")
    print(f"Maximum recovery attempts observed: {int(max_recovery)}")
    print(f"Samples with GNSS data available: {available_count}/{len(available)}")

    if failures:
        for failure in failures:
            print(failure)
        return failures

    print("PASS: capture satisfies the requested stability thresholds")
    return []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="CSV produced by tools/live_capture.py")
    parser.add_argument("--min-http-success", type=float, default=95.0)
    parser.add_argument("--min-fresh", type=float, default=90.0)
    parser.add_argument("--max-recovery-attempts", type=int)
    parser.add_argument("--max-stale-samples", type=int, default=60,
                        help="Maximum consecutive data_fresh=False samples (default: 60)")
    args = parser.parse_args(argv)
    if not 0 <= args.min_http_success <= 100 or not 0 <= args.min_fresh <= 100:
        parser.error("percentage thresholds must be between 0 and 100")
    if args.max_recovery_attempts is not None and args.max_recovery_attempts < 0:
        parser.error("max-recovery-attempts must be >= 0")
    if args.max_stale_samples < 0:
        parser.error("max-stale-samples must be >= 0")
    return 1 if analyze(args.csv, args.min_http_success, args.min_fresh, args.max_recovery_attempts, args.max_stale_samples) else 0


if __name__ == "__main__":
    raise SystemExit(main())

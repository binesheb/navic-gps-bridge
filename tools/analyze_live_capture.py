#!/usr/bin/env python3
"""Analyze a NavIC GPS Bridge /api/live capture CSV for repeatable validation."""

import argparse
import csv
import json
import math

REQUIRED_FIELDS = {"http_ok", "data_available", "data_fresh", "uptime_ms", "elapsed_s"}
NUMERIC_FIELDS = ("uptime_ms", "recovery_attempts", "elapsed_s")


def _float(row, key):
    value = row.get(key, "")
    if value in (None, ""):
        return None
    return float(value)


def _bool(row, key):
    value = row.get(key, "")
    if value is None:
        return None
    value = value.strip().lower()
    if value in ("true", "1", "yes"):
        return True
    if value in ("false", "0", "no"):
        return False
    return None


def _bool_failure(row, key, line):
    raw = row.get(key, "")
    if raw is None or not str(raw).strip():
        return f"FAIL: missing {key} value on CSV line {line}"
    return f"FAIL: invalid {key} value on CSV line {line}"


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


def _write_report(path, metrics, failures):
    report = dict(metrics)
    report["passed"] = not failures
    report["failures"] = failures
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")


def analyze(path, min_http_success=95.0, min_fresh=90.0,
            max_recovery_attempts=None, min_recovery_attempts=None,
            max_stale_samples=60, json_output=None, min_duration_s=0.0):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        rows = list(reader)

    if not REQUIRED_FIELDS.issubset(fields):
        missing = ", ".join(sorted(REQUIRED_FIELDS - fields))
        failures = [f"FAIL: capture is missing required columns: {missing}"]
        if json_output:
            _write_report(json_output, {"samples": len(rows)}, failures)
        return failures
    if not rows:
        failures = ["FAIL: capture contains no samples"]
        if json_output:
            _write_report(json_output, {"samples": 0}, failures)
        return failures

    failures = []
    for index, row in enumerate(rows, start=2):
        http_ok = _bool(row, "http_ok")
        if http_ok is None:
            failures.append(_bool_failure(row, "http_ok", index))
            continue
        # Failed HTTP requests intentionally have blank payload fields.
        for key in ("data_available", "data_fresh"):
            if http_ok and _bool(row, key) is None:
                failures.append(_bool_failure(row, key, index))
        for key in NUMERIC_FIELDS:
            if row.get(key, "") not in (None, ""):
                try:
                    value = _float(row, key)
                except ValueError:
                    failures.append(f"FAIL: invalid {key} value on CSV line {index}")
                    continue
                if value is not None and not math.isfinite(value):
                    failures.append(f"FAIL: non-finite {key} value on CSV line {index}")
        try:
            uptime = _float(row, "uptime_ms")
        except ValueError:
            uptime = None
        if uptime is None or not math.isfinite(uptime):
            failures.append(f"FAIL: invalid or missing uptime_ms value on CSV line {index}")
        try:
            elapsed = _float(row, "elapsed_s")
        except ValueError:
            elapsed = None
        if elapsed is None or not math.isfinite(elapsed):
            failures.append(f"FAIL: invalid or missing elapsed_s value on CSV line {index}")

    http_known = [_bool(r, "http_ok") for r in rows]
    http_ok_count = sum(value is True for value in http_known)
    http_rate = 100.0 * http_ok_count / len(http_known) if http_known else 0.0
    if http_rate < min_http_success:
        failures.append(f"FAIL: HTTP success {http_rate:.1f}% < {min_http_success:.1f}%")

    successful_rows = [r for r in rows if _bool(r, "http_ok") is True]
    fresh_known = [_bool(r, "data_fresh") for r in successful_rows]
    fresh = sum(value is True for value in fresh_known)
    fresh_rate = 100.0 * fresh / len(fresh_known) if fresh_known else 0.0
    if fresh_rate < min_fresh:
        failures.append(f"FAIL: fresh-data ratio {fresh_rate:.1f}% < {min_fresh:.1f}%")

    max_stale = _max_consecutive_stale(successful_rows)
    if max_stale > max_stale_samples:
        failures.append(f"FAIL: consecutive stale samples reached {max_stale} > {max_stale_samples}")

    uptimes, elapsed_values, recovery_values = [], [], []
    for row in rows:
        try:
            uptime = _float(row, "uptime_ms")
        except ValueError:
            uptime = None
        if uptime is not None and math.isfinite(uptime):
            uptimes.append(uptime)
        try:
            elapsed = _float(row, "elapsed_s")
        except ValueError:
            elapsed = None
        if elapsed is not None and math.isfinite(elapsed):
            elapsed_values.append(elapsed)
        try:
            recovery = _float(row, "recovery_attempts")
        except ValueError:
            recovery = None
        if recovery is not None and math.isfinite(recovery):
            recovery_values.append(recovery)
    if len(uptimes) >= 2 and any(b < a for a, b in zip(uptimes, uptimes[1:])):
        failures.append("FAIL: uptime_ms moved backwards; possible reboot/reset")
    if len(elapsed_values) >= 2 and any(b < a for a, b in zip(elapsed_values, elapsed_values[1:])):
        failures.append("FAIL: elapsed_s moved backwards; capture timing is inconsistent")
    if elapsed_values and elapsed_values[-1] < min_duration_s:
        failures.append(f"FAIL: capture duration {elapsed_values[-1]:.1f}s < {min_duration_s:.1f}s")
    if len(recovery_values) >= 2 and any(b < a for a, b in zip(recovery_values, recovery_values[1:])):
        failures.append("FAIL: recovery_attempts moved backwards; recovery counter is inconsistent")

    recovery_baseline = recovery_values[0] if recovery_values else 0
    recovery_end = max(recovery_values) if recovery_values else recovery_baseline
    recovery_delta = max(0, recovery_end - recovery_baseline)
    if max_recovery_attempts is not None and recovery_delta > max_recovery_attempts:
        failures.append(f"FAIL: recovery attempts during capture reached {int(recovery_delta)} > {max_recovery_attempts}")
    if min_recovery_attempts is not None and recovery_delta < min_recovery_attempts:
        failures.append(f"FAIL: recovery attempts during capture reached {int(recovery_delta)} < {min_recovery_attempts}")

    available = [_bool(r, "data_available") for r in successful_rows]
    available = [v for v in available if v is not None]
    available_count = sum(available)
    metrics = {
        "samples": len(rows),
        "http_success_percent": round(http_rate, 3),
        "fresh_data_percent": round(fresh_rate, 3),
        "max_consecutive_stale_samples": max_stale,
        "capture_duration_s": round(elapsed_values[-1], 3) if elapsed_values else 0.0,
        "recovery_attempts_during_capture": int(recovery_delta),
        "recovery_attempts_baseline": int(recovery_baseline),
        "gnss_data_available_samples": available_count,
        "successful_http_samples": len(successful_rows),
    }
    print(f"Samples: {len(rows)}")
    print(f"HTTP success: {http_rate:.1f}%")
    print(f"Fresh-data ratio: {fresh_rate:.1f}%")
    print(f"Maximum consecutive stale samples: {max_stale}")
    print(f"Capture duration: {metrics['capture_duration_s']:.1f}s")
    print(f"Recovery attempts during capture: {int(recovery_delta)} (baseline {int(recovery_baseline)})")
    print(f"Samples with GNSS data available: {available_count}/{len(available)}")
    if failures:
        for failure in failures:
            print(failure)
    else:
        print("PASS: capture satisfies the requested stability thresholds")
    if json_output:
        _write_report(json_output, metrics, failures)
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="CSV produced by tools/live_capture.py")
    parser.add_argument("--min-http-success", type=float, default=95.0)
    parser.add_argument("--min-fresh", type=float, default=90.0)
    parser.add_argument("--max-recovery-attempts", type=int)
    parser.add_argument("--min-recovery-attempts", type=int,
                        help="Require at least this many recovery attempts during this capture")
    parser.add_argument("--max-stale-samples", type=int, default=60,
                        help="Maximum consecutive data_fresh=False samples (default: 60)")
    parser.add_argument("--min-duration-s", type=float, default=0.0,
                        help="Require capture elapsed time to reach at least this many seconds")
    parser.add_argument("--json-output", help="Optional machine-readable JSON verdict path")
    args = parser.parse_args(argv)
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
    if args.min_duration_s < 0:
        parser.error("min-duration-s must be >= 0")
    return 1 if analyze(args.csv, args.min_http_success, args.min_fresh,
                        args.max_recovery_attempts, args.min_recovery_attempts,
                        args.max_stale_samples, args.json_output, args.min_duration_s) else 0


if __name__ == "__main__":
    raise SystemExit(main())

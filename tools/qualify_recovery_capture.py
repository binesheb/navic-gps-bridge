#!/usr/bin/env python3
"""Qualify a simultaneous GNSS recovery capture deterministically.

Correlates the /api/live health sequence with the timestamped NMEA connection
 timeline. It does not infer RF or position accuracy from these artifacts.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

EXPECTED = ("HEALTHY", "STALE", "RECOVERING", "HEALTHY")


def read_live(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "status" not in reader.fieldnames or "elapsed_s" not in reader.fieldnames:
            raise ValueError("live CSV must contain elapsed_s and status columns")
        rows = []
        previous = None
        for line, row in enumerate(reader, start=2):
            try:
                elapsed = float(row.get("elapsed_s", ""))
            except ValueError as exc:
                raise ValueError(f"live line {line}: invalid elapsed_s") from exc
            if not math.isfinite(elapsed):
                raise ValueError(f"live line {line}: elapsed_s must be finite")
            if previous is not None and elapsed < previous:
                raise ValueError(f"live line {line}: elapsed_s moved backwards")
            previous = elapsed
            status = (row.get("status") or row.get("health_state") or "").strip()
            rows.append((elapsed, status))
        return rows


def read_timeline(path: Path):
    events = []
    previous = None
    with path.open(encoding="utf-8") as stream:
        for line, raw in enumerate(stream, start=1):
            raw = raw.rstrip("\n")
            if not raw:
                continue
            fields = raw.split("\t", 3)
            if len(fields) != 4:
                raise ValueError(f"timeline line {line}: expected 4 tab-separated fields")
            try:
                wall = float(fields[0]); elapsed = float(fields[1])
            except ValueError as exc:
                raise ValueError(f"timeline line {line}: invalid timestamp") from exc
            if not math.isfinite(wall) or not math.isfinite(elapsed):
                raise ValueError(f"timeline line {line}: timestamps must be finite")
            if previous is not None and elapsed < previous:
                raise ValueError(f"timeline line {line}: elapsed timestamp moved backwards")
            previous = elapsed
            events.append({"wall": wall, "elapsed": elapsed, "event": fields[2], "payload": fields[3]})
    return events


def compressed(rows):
    result = []
    for elapsed, status in rows:
        if status and (not result or result[-1][1] != status):
            result.append((elapsed, status))
    return result


def recovery_sequence(rows):
    transitions = compressed(rows)
    pos = 0
    matched = []
    for row in transitions:
        if row[1] == EXPECTED[pos]:
            matched.append(row)
            pos += 1
            if pos == len(EXPECTED):
                return matched
    return None


def qualify(live_path: str, timeline_path: str, max_recovery_seconds=None,
            max_nmea_outage_seconds=None):
    live = read_live(Path(live_path))
    timeline = read_timeline(Path(timeline_path))
    matched = recovery_sequence(live)
    connections = [e for e in timeline if e["event"] == "CONNECT"]
    disconnects = [e for e in timeline if e["event"] == "DISCONNECT"]
    reconnect_pair = None
    for disconnect in disconnects:
        next_connect = next((e for e in connections if e["elapsed"] > disconnect["elapsed"]), None)
        if next_connect is not None:
            reconnect_pair = (disconnect, next_connect)
            break

    sequence_observed = matched is not None
    recovery_duration = (matched[-1][0] - matched[-2][0]) if sequence_observed else None
    outage_duration = (reconnect_pair[1]["elapsed"] - reconnect_pair[0]["elapsed"]) if reconnect_pair else None
    recovery_after_reconnect = bool(
        reconnect_pair and sequence_observed and matched[-1][0] >= reconnect_pair[1]["elapsed"]
    )
    recovery_limit_ok = max_recovery_seconds is None or (
        recovery_duration is not None and recovery_duration <= max_recovery_seconds
    )
    outage_limit_ok = max_nmea_outage_seconds is None or (
        outage_duration is not None and outage_duration <= max_nmea_outage_seconds
    )
    passed = bool(
        sequence_observed and reconnect_pair and recovery_after_reconnect
        and recovery_limit_ok and outage_limit_ok
    )
    return {
        "schema_version": 1,
        "live_samples": len(live),
        "timeline_records": len(timeline),
        "nmea_connections": len(connections),
        "nmea_disconnects": len(disconnects),
        "recovery_sequence": list(EXPECTED),
        "recovery_sequence_observed": sequence_observed,
        "recovery_duration_s": recovery_duration,
        "nmea_outage_duration_s": outage_duration,
        "recovery_after_nmea_reconnect": recovery_after_reconnect,
        "max_recovery_seconds": max_recovery_seconds,
        "recovery_duration_within_limit": recovery_limit_ok,
        "max_nmea_outage_seconds": max_nmea_outage_seconds,
        "nmea_outage_within_limit": outage_limit_ok,
        "qualification_ready": passed,
        "notes": [
            "This report correlates capture timestamps; it does not prove RF performance, position accuracy, or long-duration stability.",
            "A recovery qualification requires an observed NMEA disconnect followed by reconnect and a subsequent HEALTHY state.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("live_csv")
    parser.add_argument("nmea_timeline")
    parser.add_argument("--max-recovery-seconds", type=float)
    parser.add_argument("--max-nmea-outage-seconds", type=float)
    parser.add_argument("--json-output")
    args = parser.parse_args(argv)
    for name, value in (("max-recovery-seconds", args.max_recovery_seconds),
                        ("max-nmea-outage-seconds", args.max_nmea_outage_seconds)):
        if value is not None and (not math.isfinite(value) or value < 0):
            parser.error(f"{name} must be finite and >= 0")
    try:
        report = qualify(args.live_csv, args.nmea_timeline, args.max_recovery_seconds, args.max_nmea_outage_seconds)
    except (OSError, ValueError, csv.Error) as exc:
        parser.error(str(exc))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        Path(args.json_output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["qualification_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

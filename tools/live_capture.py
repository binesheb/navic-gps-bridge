#!/usr/bin/env python3
"""Capture /api/live telemetry from a NavIC GPS Bridge into CSV.

This dependency-free utility is intended for repeatable hardware stability and
recovery tests. It preserves missing fields as blank values so a partially
available diagnostic response is still useful evidence.
"""

import argparse
import base64
import csv
import sys
import time
import urllib.error
import urllib.request

FIELDS = [
    "timestamp_utc",
    "elapsed_s",
    "http_ok",
    "data_available",
    "data_fresh",
    "data_age_ms",
    "fix",
    "latitude",
    "longitude",
    "altitude",
    "speed_kmh",
    "satellites",
    "hdop",
    "packets",
    "invalid_packets",
    "wifi_mode",
    "uptime_ms",
    "geofence_inside",
    "geofence_events",
    "geofence_last_event_age_ms",
    "gnss_receiver_online",
    "gnss_stale",
    "gnss_age_ms",
    "gnss_accepted_sentences",
    "gnss_rejected_sentences",
    "recovery_monitoring",
    "recovery_recovering",
    "recovery_attempts",
    "recovery_last_recovery_ms",
    "recovery_last_data_ms",
    "recovery_silence_ms",
    "recovery_cooldown_ms",
    "error",
]


def _flatten(payload):
    health = payload.get("gnss_health") or {}
    recovery = payload.get("gnss_recovery") or {}
    return {
        "data_available": payload.get("data_available"),
        "data_fresh": payload.get("data_fresh"),
        "data_age_ms": payload.get("data_age_ms"),
        "fix": payload.get("fix"),
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "altitude": payload.get("altitude"),
        "speed_kmh": payload.get("speed_kmh"),
        "satellites": payload.get("satellites"),
        "hdop": payload.get("hdop"),
        "packets": payload.get("packets"),
        "invalid_packets": payload.get("invalid_packets"),
        "wifi_mode": payload.get("wifi_mode"),
        "uptime_ms": payload.get("uptime_ms"),
        "geofence_inside": payload.get("geofence_inside"),
        "geofence_events": payload.get("geofence_events"),
        "geofence_last_event_age_ms": payload.get("geofence_last_event_age_ms"),
        "gnss_receiver_online": health.get("receiver_online"),
        "gnss_stale": health.get("stale"),
        "gnss_age_ms": health.get("age_ms"),
        "gnss_accepted_sentences": health.get("accepted_sentences"),
        "gnss_rejected_sentences": health.get("rejected_sentences"),
        "recovery_monitoring": recovery.get("monitoring"),
        "recovery_recovering": recovery.get("recovering"),
        "recovery_attempts": recovery.get("attempts"),
        "recovery_last_recovery_ms": recovery.get("last_recovery_ms"),
        "recovery_last_data_ms": recovery.get("last_data_ms"),
        "recovery_silence_ms": recovery.get("silence_ms"),
        "recovery_cooldown_ms": recovery.get("cooldown_ms"),
    }


def fetch_live(url, username=None, password=None, timeout=5):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    if username is not None:
        token = base64.b64encode(f"{username}:{password or ''}".encode()).decode()
        request.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        import json
        return response.status, json.loads(response.read().decode("utf-8"))


def capture(base_url, output, interval, duration, username=None, password=None, timeout=5):
    url = base_url.rstrip("/") + "/api/live"
    started = time.monotonic()
    deadline = None if duration <= 0 else started + duration
    samples = 0
    failures = 0

    with open(output, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        while deadline is None or time.monotonic() < deadline:
            sample_started = time.monotonic()
            row = {field: "" for field in FIELDS}
            row["timestamp_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            row["elapsed_s"] = f"{sample_started - started:.3f}"
            try:
                status, payload = fetch_live(url, username, password, timeout)
                row["http_ok"] = status == 200
                row.update(_flatten(payload))
                samples += 1
            except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
                failures += 1
                row["http_ok"] = False
                row["error"] = str(exc)
            writer.writerow(row)
            stream.flush()

            if deadline is not None and time.monotonic() >= deadline:
                break
            sleep_for = interval - (time.monotonic() - sample_started)
            if sleep_for > 0:
                time.sleep(sleep_for)

    return samples, failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="Bridge URL, e.g. http://192.168.4.1")
    parser.add_argument("output", help="CSV output path")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between samples (default: 1)")
    parser.add_argument("--duration", type=float, default=1800, help="Capture duration in seconds; 0 means until interrupted")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds (default: 5)")
    args = parser.parse_args(argv)
    if args.interval <= 0 or args.timeout <= 0 or args.duration < 0:
        parser.error("interval and timeout must be > 0; duration must be >= 0")
    try:
        samples, failures = capture(args.base_url, args.output, args.interval, args.duration, args.username, args.password, args.timeout)
    except KeyboardInterrupt:
        print("Capture interrupted; partial CSV retained.", file=sys.stderr)
        return 130
    print(f"Captured {samples} samples with {failures} request failure(s) to {args.output}")
    return 0 if samples else 1


if __name__ == "__main__":
    raise SystemExit(main())

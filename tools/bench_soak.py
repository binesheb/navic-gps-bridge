#!/usr/bin/env python3
"""Run repeated first-bench bridge checks and emit machine-readable evidence.

This dependency-free helper detects intermittent GNSS freshness or TCP NMEA
failures that a single smoke sample can miss. It is a bring-up aid and does
not claim physical NavIC reception or H01-H14 qualification.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from bench_smoke import read_live, read_nmea


def run(
    base_url: str,
    tcp_host: str,
    tcp_port: int,
    samples: int,
    interval: float,
    timeout: float,
    max_age_ms: int,
    min_nmea_sentences: int = 1,
) -> dict:
    observations = []
    started_at_ms = int(time.time() * 1000)
    for index in range(samples):
        started = time.monotonic()
        errors = []
        live = None
        total = valid = 0
        try:
            live = read_live(base_url, min(timeout, 5.0), max_age_ms)
        except Exception as exc:  # noqa: BLE001 - evidence must include transport failures
            errors.append(f"HTTP diagnostics: {exc}")
        try:
            total, valid = read_nmea(tcp_host, tcp_port, timeout)
        except OSError as exc:
            errors.append(f"TCP NMEA: {exc}")
        checksum_valid = total > 0 and total == valid
        if total < min_nmea_sentences:
            errors.append(f"TCP NMEA: only {total} sentences observed; minimum is {min_nmea_sentences}")
        observations.append({
            "sample": index + 1,
            "observed_at_unix_ms": int(time.time() * 1000),
            "passed": not errors and checksum_valid,
            "http_live": live,
            "nmea_sentences": total,
            "nmea_valid_sentences": valid,
            "nmea_checksum_valid": checksum_valid,
            "nmea_valid_percent": round((valid / total) * 100, 2) if total else 0.0,
            "errors": errors,
            "duration_s": round(time.monotonic() - started, 3),
        })
        if index + 1 < samples:
            time.sleep(interval)

    passed_samples = sum(item["passed"] for item in observations)
    return {
        "schema": 3,
        "started_at_unix_ms": started_at_ms,
        "ended_at_unix_ms": int(time.time() * 1000),
        "passed": passed_samples == samples,
        "samples": samples,
        "passed_samples": passed_samples,
        "failed_samples": samples - passed_samples,
        "max_data_age_ms": max_age_ms,
        "min_nmea_sentences": min_nmea_sentences,
        "observations": observations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--tcp-host")
    parser.add_argument("--tcp-port", type=int, default=10110)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-data-age-ms", type=int, default=3000)
    parser.add_argument("--min-nmea-sentences", type=int, default=1)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    if (
        args.samples <= 0
        or args.interval < 0
        or args.timeout <= 0
        or args.max_data_age_ms <= 0
        or args.min_nmea_sentences <= 0
        or not 1024 <= args.tcp_port <= 65535
    ):
        parser.error("samples > 0; interval >= 0; timeout/max-data-age-ms/min-nmea-sentences > 0; tcp-port 1024..65535")
    host = args.tcp_host
    if not host:
        from bench_smoke import base_host
        host = base_host(args.base_url)
    result = run(
        args.base_url,
        host,
        args.tcp_port,
        args.samples,
        args.interval,
        args.timeout,
        args.max_data_age_ms,
        args.min_nmea_sentences,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

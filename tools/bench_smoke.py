#!/usr/bin/env python3
"""Run a dependency-free first-bench smoke check against a live bridge.

The check verifies that the HTTP diagnostics endpoint responds with a usable
and fresh live snapshot and that the TCP NMEA service emits at least one
checksum-valid sentence during the same observation window. It is a bring-up
aid, not a physical qualification or NavIC reception claim.
"""

from __future__ import annotations

import argparse
import json
import math
import socket
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


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


def validate_live(payload: dict, max_age_ms: int) -> None:
    if not isinstance(payload, dict):
        raise RuntimeError("/api/live did not return a JSON object")
    required = ("fix", "satellites", "latitude", "longitude", "data_available", "data_fresh", "data_age_ms")
    missing = [key for key in required if key not in payload]
    if missing:
        raise RuntimeError("/api/live missing fields: " + ", ".join(missing))
    if not isinstance(payload["fix"], bool):
        raise RuntimeError("/api/live fix must be boolean")
    if not isinstance(payload["data_available"], bool) or not payload["data_available"]:
        raise RuntimeError("/api/live reports no GNSS data")
    if not isinstance(payload["data_fresh"], bool) or not payload["data_fresh"]:
        raise RuntimeError("/api/live reports stale GNSS data")
    satellites = payload["satellites"]
    if isinstance(satellites, bool) or not isinstance(satellites, (int, float)) or satellites < 0 or not float(satellites).is_integer():
        raise RuntimeError(f"/api/live satellites value {satellites!r} is invalid")
    latitude = payload["latitude"]
    longitude = payload["longitude"]
    if not isinstance(latitude, (int, float)) or isinstance(latitude, bool) or not math.isfinite(latitude) or not -90.0 <= latitude <= 90.0:
        raise RuntimeError(f"/api/live latitude {latitude!r} is invalid")
    if not isinstance(longitude, (int, float)) or isinstance(longitude, bool) or not math.isfinite(longitude) or not -180.0 <= longitude <= 180.0:
        raise RuntimeError(f"/api/live longitude {longitude!r} is invalid")
    age_ms = payload["data_age_ms"]
    if isinstance(age_ms, bool) or not isinstance(age_ms, (int, float)) or not math.isfinite(age_ms) or age_ms < 0 or age_ms > max_age_ms:
        raise RuntimeError(f"/api/live data age {age_ms} ms exceeds {max_age_ms} ms")


def read_live(base_url: str, timeout: float, max_age_ms: int) -> dict:
    with urlopen(base_url.rstrip("/") + "/api/live", timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"/api/live returned HTTP {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
    validate_live(payload, max_age_ms)
    return payload


def read_nmea(host: str, port: int, timeout: float) -> tuple[int, int]:
    total = valid = 0
    with socket.create_connection((host, port), timeout=timeout) as client:
        client.settimeout(timeout)
        buffer = b""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                chunk = client.recv(4096)
            except socket.timeout:
                break
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                raw, buffer = buffer.split(b"\n", 1)
                text = raw.decode("ascii", errors="replace").strip("\r")
                if not text.startswith("$"):
                    continue
                total += 1
                valid += checksum_ok(text)
    return total, valid


def run(base_url: str, tcp_host: str, tcp_port: int, timeout: float, max_age_ms: int) -> dict:
    started = time.monotonic()
    errors: list[str] = []
    live: dict | None = None
    total = valid = 0
    try:
        live = read_live(base_url, min(timeout, 5.0), max_age_ms)
    except (OSError, ValueError, RuntimeError, URLError) as exc:
        errors.append(f"HTTP diagnostics: {exc}")
    try:
        total, valid = read_nmea(tcp_host, tcp_port, timeout)
    except OSError as exc:
        errors.append(f"TCP NMEA: {exc}")
    duration = time.monotonic() - started
    return {
        "schema": 2,
        "passed": not errors and total > 0 and total == valid,
        "duration_s": round(duration, 3),
        "http_live": live,
        "nmea_sentences": total,
        "nmea_valid_sentences": valid,
        "nmea_checksum_valid": total > 0 and total == valid,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="bridge URL, e.g. http://192.168.4.1")
    parser.add_argument("--tcp-host", help="TCP NMEA host; defaults to URL hostname")
    parser.add_argument("--tcp-port", type=int, default=10110)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-data-age-ms", type=int, default=3000)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.max_data_age_ms <= 0 or not 1024 <= args.tcp_port <= 65535:
        parser.error("timeout and max-data-age-ms must be > 0 and tcp-port must be 1024..65535")
    host = args.tcp_host or base_host(args.base_url)
    result = run(args.base_url, host, args.tcp_port, args.timeout, args.max_data_age_ms)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


def base_host(base_url: str) -> str:
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    if not parsed.hostname:
        raise ValueError("base URL must include a hostname")
    return parsed.hostname


if __name__ == "__main__":
    raise SystemExit(main())

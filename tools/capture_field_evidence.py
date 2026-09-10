#!/usr/bin/env python3
"""Capture HTTP live diagnostics and TCP NMEA evidence in one time window."""
from __future__ import annotations
import argparse
import csv
import json
import socket
import threading
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen


def parse_bridge_host(base_url: str) -> str:
    """Return a socket-safe hostname from an HTTP(S) bridge URL."""
    try:
        parsed = urlsplit(base_url)
    except ValueError as exc:
        raise ValueError(f"invalid bridge URL: {exc}") from exc
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("bridge URL must use http or https")
    if not parsed.hostname:
        raise ValueError("bridge URL must contain a hostname")
    # URL zone identifiers are percent-encoded (e.g. %25eth0); socket APIs
    # expect the decoded scope form (e.g. %eth0).
    return unquote(parsed.hostname)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("base_url")
    p.add_argument("output_dir")
    p.add_argument("--duration", type=float, default=60.0)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--nmea-port", type=int, default=10110)
    p.add_argument("--timeout", type=float, default=3.0)
    p.add_argument("--reconnect-interval", type=float, default=1.0,
                   help="seconds to wait before retrying a disconnected NMEA stream")
    p.add_argument("--quality-gate", action="store_true",
                   help="validate the completed capture against quality thresholds")
    p.add_argument("--max-http-errors", type=int, default=0)
    p.add_argument("--max-nmea-reconnects", type=int, default=0)
    p.add_argument("--min-live-rate-hz", type=float, default=0.5)
    p.add_argument("--min-nmea-sentences", type=int, default=1)
    a = p.parse_args(argv)
    if a.duration <= 0 or a.interval <= 0 or a.timeout <= 0 or a.reconnect_interval <= 0:
        p.error("duration, interval, timeout, and reconnect-interval must be > 0")
    if not 1 <= a.nmea_port <= 65535:
        p.error("nmea-port must be between 1 and 65535")
    if a.max_http_errors < 0 or a.max_nmea_reconnects < 0 or a.min_nmea_sentences < 0:
        p.error("quality count thresholds must be >= 0")
    if a.min_live_rate_hz <= 0:
        p.error("min-live-rate-hz must be > 0")
    try:
        host = parse_bridge_host(a.base_url)
    except ValueError as exc:
        p.error(str(exc))

    out = Path(a.output_dir); out.mkdir(parents=True, exist_ok=True)
    live_path = out / "live.csv"
    nmea_path = out / "nmea.log"
    timeline_path = out / "nmea_timeline.log"
    meta_path = out / "CAPTURE.json"
    quality_path = out / "CAPTURE_QUALITY.json"
    stop = threading.Event(); errors = []
    start = time.monotonic(); wall_start = time.time()
    nmea_count = 0
    nmea_connections = 0
    nmea_reconnects = 0
    nmea_disconnects = 0
    timeline_records = 0
    lock = threading.Lock()

    def timeline(event, payload=""):
        nonlocal timeline_records
        elapsed = time.monotonic() - start
        wall = wall_start + elapsed
        with timeline_path.open("a", encoding="utf-8") as f:
            f.write(f"{wall:.3f}\t{elapsed:.3f}\t{event}\t{payload}\n")
        with lock:
            timeline_records += 1

    def nmea_worker():
        nonlocal nmea_count, nmea_connections, nmea_reconnects, nmea_disconnects
        first_connection = True
        while not stop.is_set():
            try:
                with socket.create_connection((host, a.nmea_port), timeout=a.timeout) as s, nmea_path.open("a", encoding="utf-8") as f:
                    with lock:
                        nmea_connections += 1
                        if not first_connection:
                            nmea_reconnects += 1
                    timeline("CONNECT", f"port={a.nmea_port}")
                    first_connection = False
                    s.settimeout(0.5); buf = b""
                    while not stop.is_set():
                        try: buf += s.recv(4096)
                        except socket.timeout: continue
                        if not buf: break
                        while b"\n" in buf:
                            line, buf = buf.split(b"\n", 1)
                            text = line.decode("ascii", "replace").rstrip("\r")
                            f.write(text + "\n"); f.flush()
                            if text.startswith("$"):
                                with lock: nmea_count += 1
                                timeline("NMEA", text)
                    if not stop.is_set():
                        with lock: nmea_disconnects += 1
                        timeline("DISCONNECT", "peer_closed")
            except Exception as exc:
                if not stop.is_set():
                    with lock: nmea_disconnects += 1
                    timeline("DISCONNECT", str(exc).replace("\t", " "))
                    errors.append(f"NMEA: {exc}")
            if not stop.is_set():
                stop.wait(a.reconnect_interval)

    timeline_path.write_text("", encoding="utf-8")
    t = threading.Thread(target=nmea_worker, daemon=True); t.start()
    fields = ["elapsed_s", "timestamp", "fix", "latitude", "longitude", "altitude_m", "speed_kmh", "satellites", "health_state"]
    samples = 0
    http_errors = 0
    with live_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        while time.monotonic() - start < a.duration:
            elapsed = time.monotonic() - start
            try:
                req = Request(a.base_url.rstrip("/") + "/api/live", headers={"Cache-Control": "no-cache"})
                with urlopen(req, timeout=a.timeout) as r: data = json.load(r)
                row = {k: data.get(k, "") for k in fields if k not in ("elapsed_s", "timestamp")}
                row["elapsed_s"] = f"{elapsed:.3f}"; row["timestamp"] = f"{wall_start + elapsed:.3f}"
                writer.writerow(row); f.flush(); samples += 1
            except Exception as exc:
                http_errors += 1; errors.append(f"HTTP: {exc}")
            stop.wait(a.interval)
    stop.set(); t.join(timeout=max(1.0, a.timeout + a.reconnect_interval + 0.5))
    report = {"schema_version": 2, "base_url": a.base_url, "duration_s": a.duration, "interval_s": a.interval,
              "started_unix_s": wall_start, "live_samples": samples, "http_errors": http_errors,
              "nmea_sentences": nmea_count, "nmea_port": a.nmea_port, "nmea_connections": nmea_connections,
              "nmea_reconnects": nmea_reconnects, "nmea_disconnects": nmea_disconnects,
              "nmea_timeline_records": timeline_records, "nmea_timeline": "nmea_timeline.log",
              "errors": errors, "simultaneous_window": True}
    meta_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    quality_passed = True
    if a.quality_gate:
        try:
            from validate_capture_quality import evaluate
            quality = evaluate(report, max_http_errors=a.max_http_errors,
                               max_nmea_reconnects=a.max_nmea_reconnects,
                               min_live_rate=a.min_live_rate_hz,
                               min_nmea_sentences=a.min_nmea_sentences)
        except (ImportError, KeyError, TypeError, ValueError) as exc:
            quality = {"schema_version": 1, "passed": False,
                       "failures": [f"quality gate error: {exc}"]}
        quality_path.write_text(json.dumps(quality, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        quality_passed = quality.get("passed") is True
        print(json.dumps(quality, indent=2, sort_keys=True))

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if samples and nmea_count and quality_passed else 1

if __name__ == "__main__":
    raise SystemExit(main())

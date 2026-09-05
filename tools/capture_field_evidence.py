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
from urllib.request import Request, urlopen


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("base_url")
    p.add_argument("output_dir")
    p.add_argument("--duration", type=float, default=60.0)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--nmea-port", type=int, default=10110)
    p.add_argument("--timeout", type=float, default=3.0)
    a = p.parse_args(argv)
    if a.duration <= 0 or a.interval <= 0 or a.timeout <= 0:
        p.error("duration, interval, and timeout must be > 0")
    if not 1 <= a.nmea_port <= 65535:
        p.error("nmea-port must be between 1 and 65535")

    out = Path(a.output_dir); out.mkdir(parents=True, exist_ok=True)
    live_path, nmea_path, meta_path = out / "live.csv", out / "nmea.log", out / "CAPTURE.json"
    stop = threading.Event(); errors = []
    start = time.monotonic(); wall_start = time.time()
    nmea_count = 0
    lock = threading.Lock()

    host = a.base_url.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]

    def nmea_worker():
        nonlocal nmea_count
        try:
            with socket.create_connection((host, a.nmea_port), timeout=a.timeout) as s, nmea_path.open("w", encoding="utf-8") as f:
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
        except Exception as exc:
            errors.append(f"NMEA: {exc}")

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
    stop.set(); t.join(timeout=max(1.0, a.timeout + 0.5))
    report = {"schema_version": 1, "base_url": a.base_url, "duration_s": a.duration, "interval_s": a.interval,
              "started_unix_s": wall_start, "live_samples": samples, "http_errors": http_errors,
              "nmea_sentences": nmea_count, "nmea_port": a.nmea_port, "errors": errors,
              "simultaneous_window": True}
    meta_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if samples and nmea_count else 1

if __name__ == "__main__":
    raise SystemExit(main())

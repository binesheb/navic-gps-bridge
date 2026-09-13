#!/usr/bin/env python3
"""Regression tests for validate_capture_quality."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from validate_capture_quality import evaluate
from validate_field_capture import validate_capture


def _run_dir(**overrides):
    report = {
        "schema_version": 2,
        "simultaneous_window": True,
        "nmea_timeline": "nmea_timeline.log",
        "duration_s": 10.0,
        "interval_s": 1.0,
        "live_samples": 10,
        "nmea_sentences": 20,
        "nmea_port": 10110,
        "nmea_connections": 1,
        "nmea_reconnects": 0,
        "nmea_timeline_records": 21,
        "http_errors": 0,
    }
    report.update(overrides)
    run = Path(tempfile.mkdtemp())
    (run / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
    live_rows = [f"2026-09-13T00:00:{i:02d}Z,10.0,76.0" for i in range(10)]
    (run / "live.csv").write_text("timestamp,lat,lon\n" + "\n".join(live_rows) + "\n", encoding="utf-8")
    (run / "nmea.log").write_text("$GPGGA,1\n" * 20, encoding="utf-8")
    (run / "nmea_timeline.log").write_text("timeline\n" * 21, encoding="utf-8")
    return run, report


def main() -> int:
    run, _ = _run_dir()
    report = validate_capture(run)
    result = evaluate(report, max_http_errors=0, max_nmea_reconnects=0,
                      min_live_rate=0.5, min_nmea_sentences=1)
    assert result["passed"]
    assert result["live_rate_hz"] == 1.0

    _, report = _run_dir(http_errors=1)
    result = evaluate(report, max_http_errors=0, max_nmea_reconnects=0,
                      min_live_rate=0.5, min_nmea_sentences=1)
    assert not result["passed"]
    assert "http_errors" in result["failures"][0]

    _, report = _run_dir(nmea_reconnects=1)
    result = evaluate(report, max_http_errors=0, max_nmea_reconnects=0,
                      min_live_rate=0.5, min_nmea_sentences=1)
    assert not result["passed"]
    assert "nmea_reconnects" in result["failures"][0]

    _, report = _run_dir(live_samples=2)
    result = evaluate(report, max_http_errors=0, max_nmea_reconnects=0,
                      min_live_rate=0.5, min_nmea_sentences=1)
    assert not result["passed"]
    assert "live_rate_hz" in result["failures"][0]
    print("validate_capture_quality tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

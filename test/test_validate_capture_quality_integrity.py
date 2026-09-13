from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from validate_capture_quality import evaluate


def base_report():
    return {
        "duration_s": 10.0,
        "live_samples": 10,
        "nmea_sentences": 20,
        "http_errors": 0,
        "nmea_connections": 1,
        "nmea_reconnects": 0,
    }


def test_accepts_consistent_capture():
    result = evaluate(base_report(), max_http_errors=0, max_nmea_reconnects=0,
                      min_live_rate=0.5, min_nmea_sentences=1)
    assert result["passed"] is True
    assert result["live_rate_hz"] == 1.0


def test_rejects_more_reconnects_than_connections_allow():
    report = base_report()
    report["nmea_connections"] = 2
    report["nmea_reconnects"] = 2
    result = evaluate(report, max_http_errors=10, max_nmea_reconnects=10,
                      min_live_rate=0.5, min_nmea_sentences=1)
    assert result["passed"] is False
    assert any("exceeds possible reconnects" in failure for failure in result["failures"])


def test_rejects_zero_duration_without_division_error():
    report = base_report()
    report["duration_s"] = 0
    result = evaluate(report, max_http_errors=0, max_nmea_reconnects=0,
                      min_live_rate=0.5, min_nmea_sentences=1)
    assert result["passed"] is False
    assert result["live_rate_hz"] == 0.0
    assert any("duration_s" in failure for failure in result["failures"])

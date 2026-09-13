from tools.validate_capture_quality import evaluate


def base_report():
    return {
        "schema_version": 2,
        "simultaneous_window": True,
        "nmea_timeline": "nmea_timeline.log",
        "duration_s": 10.0,
        "interval_s": 1.0,
        "live_samples": 10,
        "nmea_sentences": 20,
        "nmea_connections": 1,
        "nmea_reconnects": 0,
        "http_errors": 0,
    }


def test_interrupted_capture_never_passes_quality_gate():
    report = base_report()
    report["interrupted"] = True

    result = evaluate(
        report,
        max_http_errors=0,
        max_nmea_reconnects=0,
        min_live_rate=0.5,
        min_nmea_sentences=1,
    )

    assert result["passed"] is False
    assert result["interrupted"] is True
    assert any("interrupted" in failure for failure in result["failures"])


def test_completed_capture_remains_eligible():
    report = base_report()
    report["interrupted"] = False

    result = evaluate(
        report,
        max_http_errors=0,
        max_nmea_reconnects=0,
        min_live_rate=0.5,
        min_nmea_sentences=1,
    )

    assert result["passed"] is True
    assert result["failures"] == []

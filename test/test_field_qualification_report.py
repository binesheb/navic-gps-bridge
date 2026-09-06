from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import field_qualification_report as report


def sample():
    return {
        "schema_version": 1,
        "qualification_ready": True,
        "passed": True,
        "health_sequence": ["HEALTHY", "STALE", "RECOVERING", "HEALTHY"],
        "recovery": {"duration_s": 2.5},
        "nmea_outage": {"duration_s": 1.75, "disconnect_count": 1, "connect_count": 1},
        "evidence_sha256": {
            "CAPTURE.json": "a" * 64,
            "live.csv": "b" * 64,
            "nmea_timeline.log": "c" * 64,
        },
    }


def test_render_includes_verdict_and_evidence():
    text = report.render(sample())
    assert "**Result:** PASS" in text
    assert "Recovery duration: 2.500 s" in text
    assert "`CAPTURE.json`: `" + "a" * 64 in text


def test_render_can_include_verification():
    text = report.render(sample(), {"passed": True})
    assert "Evidence hashes match: yes" in text


def test_render_includes_test_identity():
    text = report.render(sample(), metadata={
        "device": "bridge-01",
        "firmware_commit": "abc123",
        "receiver": "u-blox M10",
        "test_id": "2026-09-06-recovery-01",
    })
    assert "**Device:** `bridge-01`" in text
    assert "**Firmware commit:** `abc123`" in text
    assert "**GNSS receiver:** `u-blox M10`" in text
    assert "**Test ID:** `2026-09-06-recovery-01`" in text


def test_rejects_invalid_metadata_value():
    try:
        report.render(sample(), metadata={"device": "   "})
    except ValueError as exc:
        assert "metadata[device]" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_rejects_non_ready_report():
    value = sample()
    value["qualification_ready"] = False
    try:
        report.render(value)
    except ValueError as exc:
        assert "not qualification-ready" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_rejects_wrong_schema():
    value = sample()
    value["schema_version"] = 2
    try:
        report.render(value)
    except ValueError as exc:
        assert "schema_version" in str(exc)
    else:
        raise AssertionError("expected ValueError")
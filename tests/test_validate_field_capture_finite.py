import json

import pytest

from tools.validate_field_capture import validate_capture


REQUIRED = {
    "schema_version": 2,
    "simultaneous_window": True,
    "duration_s": 60.0,
    "interval_s": 1.0,
    "live_samples": 60,
    "nmea_sentences": 60,
    "nmea_connections": 1,
    "nmea_timeline_records": 61,
    "nmea_port": 10110,
}


def make_run(tmp_path, **overrides):
    run = tmp_path / "capture"
    run.mkdir()
    (run / "CAPTURE.json").write_text(
        json.dumps({**REQUIRED, **overrides}), encoding="utf-8"
    )
    for name in ("live.csv", "nmea.log", "nmea_timeline.log"):
        (run / name).write_text("data\n", encoding="utf-8")
    return run


@pytest.mark.parametrize("key,value", [("duration_s", float("nan")), ("interval_s", float("inf"))])
def test_rejects_non_finite_timing_metadata(tmp_path, key, value):
    run = make_run(tmp_path, **{key: value})
    with pytest.raises(ValueError, match=f"{key} must be a positive finite number"):
        validate_capture(run)


def test_accepts_finite_timing_metadata(tmp_path):
    report = validate_capture(make_run(tmp_path))
    assert report["duration_s"] == 60.0
    assert report["interval_s"] == 1.0

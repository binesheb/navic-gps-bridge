from pathlib import Path

import pytest

from tools.validate_field_capture import validate_capture


def write_bundle(tmp_path: Path, *, live_samples=2, nmea_sentences=2, timeline_records=3):
    run = tmp_path / "capture"
    run.mkdir()
    (run / "live.csv").write_text("elapsed_s,fix\n0.0,1\n1.0,1\n", encoding="utf-8")
    (run / "nmea.log").write_text("$GPGGA,one\n$GPRMC,two\n", encoding="utf-8")
    (run / "nmea_timeline.log").write_text(
        "1.0\t0.0\tCONNECT\tport=10110\n"
        "1.1\t0.1\tNMEA\t$GPGGA,one\n"
        "1.2\t0.2\tNMEA\t$GPRMC,two\n",
        encoding="utf-8",
    )
    (run / "CAPTURE.json").write_text(
        '{\n'
        '  "schema_version": 2,\n'
        '  "simultaneous_window": true,\n'
        '  "nmea_timeline": "nmea_timeline.log",\n'
        f'  "duration_s": 2, "interval_s": 1, "live_samples": {live_samples},\n'
        f'  "nmea_sentences": {nmea_sentences}, "nmea_connections": 1,\n'
        f'  "nmea_timeline_records": {timeline_records}, "nmea_port": 10110\n'
        '}\n',
        encoding="utf-8",
    )
    return run


def test_accepts_matching_capture_counts(tmp_path):
    validate_capture(write_bundle(tmp_path))


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("live_samples", 1, "live_samples does not match live.csv rows"),
        ("nmea_sentences", 1, "nmea_sentences does not match nmea.log"),
        ("nmea_timeline_records", 2, "nmea_timeline_records does not match nmea_timeline.log"),
    ],
)
def test_rejects_count_mismatch(tmp_path, field, value, expected):
    run = write_bundle(tmp_path)
    text = (run / "CAPTURE.json").read_text(encoding="utf-8")
    text = text.replace(f'"{field}": {value + 1}', f'"{field}": {value}')
    (run / "CAPTURE.json").write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=expected):
        validate_capture(run)

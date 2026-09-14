import json
from pathlib import Path

import pytest

from tools.finalize_capture_integrity import finalize


def make_capture(tmp_path: Path) -> Path:
    run = tmp_path / "capture"
    run.mkdir()
    (run / "CAPTURE.json").write_text(json.dumps({"schema_version": 2, "live_samples": 10}) + "\n", encoding="utf-8")
    (run / "live.csv").write_text("elapsed_s,timestamp\n0,1\n", encoding="utf-8")
    (run / "nmea.log").write_text("$GNGGA,example*00\n", encoding="utf-8")
    (run / "nmea_timeline.log").write_text("1.0\t0.0\tCONNECT\tport=10110\n", encoding="utf-8")
    return run


def test_finalize_records_hashes_and_sizes(tmp_path):
    run = make_capture(tmp_path)
    report = finalize(run)

    integrity = report["evidence_integrity"]
    assert integrity["schema"] == 1
    assert integrity["hash_algorithm"] == "SHA-256"
    assert integrity["self_excluded"] is True
    assert [item["name"] for item in integrity["files"]] == ["live.csv", "nmea.log", "nmea_timeline.log"]
    for item in integrity["files"]:
        assert item["bytes"] == (run / item["name"]).stat().st_size
        assert len(item["sha256"]) == 64


def test_finalize_includes_optional_quality_and_preflight(tmp_path):
    run = make_capture(tmp_path)
    (run / "CAPTURE_QUALITY.json").write_text('{"passed": true}\n', encoding="utf-8")
    (run / "HARDWARE_PREFLIGHT.json").write_text('{"passed": true}\n', encoding="utf-8")

    report = finalize(run)
    names = [item["name"] for item in report["evidence_integrity"]["files"]]
    assert names == ["live.csv", "nmea.log", "nmea_timeline.log", "CAPTURE_QUALITY.json", "HARDWARE_PREFLIGHT.json"]


def test_finalize_rejects_missing_required_evidence(tmp_path):
    run = make_capture(tmp_path)
    (run / "nmea.log").unlink()

    with pytest.raises(ValueError, match="required evidence file does not exist: nmea.log"):
        finalize(run)


def test_finalize_rejects_symlink_evidence(tmp_path):
    run = make_capture(tmp_path)
    target = tmp_path / "outside.csv"
    target.write_text("outside\n", encoding="utf-8")
    (run / "live.csv").unlink()
    (run / "live.csv").symlink_to(target)

    with pytest.raises(ValueError, match="missing or is a symlink: live.csv"):
        finalize(run)

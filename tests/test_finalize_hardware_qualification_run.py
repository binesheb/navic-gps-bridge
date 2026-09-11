import json

import pytest

from tools.finalize_hardware_qualification_run import validate_recovery_evidence, validate_required_files
from tools.verify_recovery_report import sha256_file


def _write_bundle(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    for name, content in {
        "CAPTURE.json": '{"schema_version": 1, "qualification_ready": true}\n',
        "live.csv": "0,ok\n",
        "nmea_timeline.log": "0,GNRMC\n",
    }.items():
        (run / name).write_text(content, encoding="utf-8")
    hashes = {name: sha256_file(run / name) for name in ("CAPTURE.json", "live.csv", "nmea_timeline.log")}
    report = {"schema_version": 1, "qualification_ready": True, "passed": True, "evidence_sha256": hashes}
    (run / "recovery-qualification.json").write_text(json.dumps(report), encoding="utf-8")
    verification = {
        "passed": True,
        "evidence": {
            name: {"expected": digest, "actual": digest, "match": True}
            for name, digest in hashes.items()
        },
    }
    (run / "recovery-verification.json").write_text(json.dumps(verification), encoding="utf-8")
    return run


def test_rechecks_recovery_hashes_and_accepts_current_verdict(tmp_path):
    run = _write_bundle(tmp_path)
    validate_recovery_evidence(run)


def test_rejects_changed_recovery_evidence(tmp_path):
    run = _write_bundle(tmp_path)
    (run / "live.csv").write_text("0,changed\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="no longer matches"):
        validate_recovery_evidence(run)


def test_rejects_stale_verification_artifact(tmp_path):
    run = _write_bundle(tmp_path)
    (run / "recovery-verification.json").write_text('{"passed": true, "evidence": {}}\n', encoding="utf-8")
    with pytest.raises(SystemExit, match="stale"):
        validate_recovery_evidence(run)


def test_rejects_symlinked_required_evidence(tmp_path):
    run = _write_bundle(tmp_path)
    (run / "FIELD_ACCEPTANCE.json").symlink_to(run / "recovery-qualification.json")
    with pytest.raises(SystemExit, match="must not be symlinks"):
        validate_required_files(run)


def test_accepts_regular_required_evidence(tmp_path):
    run = _write_bundle(tmp_path)
    for name in (
        "nmea-verdict.json",
        "serial.log",
        "EVIDENCE_MANIFEST.json",
        "FIELD_ACCEPTANCE.json",
        "FIELD_QUALIFICATION.md",
        "FIELD_QUALIFICATION_RESULT.json",
    ):
        (run / name).write_text("evidence\n", encoding="utf-8")
    validate_required_files(run)

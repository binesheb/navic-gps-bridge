import hashlib
import json
from pathlib import Path

import pytest

from tools.verify_field_evidence import verify_bundle


def write_manifest(run: Path, name: str = "capture.log") -> None:
    payload = b"GNSS evidence\n"
    (run / name).write_bytes(payload)
    manifest = {
        "schema": 1,
        "firmware_commit": "test-commit",
        "files": [{"name": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}],
    }
    (run / "EVIDENCE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_rejects_symlinked_evidence_file(tmp_path: Path):
    run = tmp_path / "bundle"
    run.mkdir()
    write_manifest(run)
    target = run / "capture.log"
    target.unlink()
    source = tmp_path / "outside.log"
    source.write_text("GNSS evidence\n", encoding="utf-8")
    try:
        target.symlink_to(source)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    failures = verify_bundle(run)
    assert failures == ["evidence file must not be a symlink: capture.log"]


def test_rejects_symlinked_manifest(tmp_path: Path):
    run = tmp_path / "bundle"
    run.mkdir()
    write_manifest(run)
    manifest = run / "EVIDENCE_MANIFEST.json"
    real_manifest = tmp_path / "manifest.json"
    real_manifest.write_text(manifest.read_text(encoding="utf-8"), encoding="utf-8")
    manifest.unlink()
    try:
        manifest.symlink_to(real_manifest)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    failures = verify_bundle(run)
    assert failures == ["manifest must not be a symlink: EVIDENCE_MANIFEST.json"]

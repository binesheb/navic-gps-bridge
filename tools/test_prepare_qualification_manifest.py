from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.create_hardware_qualification_run import EVIDENCE_FILES
from tools.prepare_qualification_manifest import prepare_manifest


def write_run(tmp_path: Path, *, identity: dict | None = None, empty: tuple[str, ...] = ()) -> Path:
    run = tmp_path / "run"
    run.mkdir()
    values = {
        "device": "bridge-01",
        "firmware_commit": "abc123",
        "receiver": "receiver-x",
        "test_id": "HARDWARE-001",
    }
    if identity:
        values.update(identity)
    (run / "RUN_METADATA.json").write_text(json.dumps(values), encoding="utf-8")
    for name in EVIDENCE_FILES:
        if name == "EVIDENCE_MANIFEST.json":
            continue
        (run / name).write_text("evidence\n" if name not in empty else "", encoding="utf-8")
    return run


def test_prepare_manifest_uses_run_identity_and_all_required_files(tmp_path: Path) -> None:
    run = write_run(tmp_path)
    manifest = prepare_manifest(run)

    assert manifest["device"] == "bridge-01"
    assert manifest["firmware_commit"] == "abc123"
    assert manifest["receiver"] == "receiver-x"
    assert manifest["test_id"] == "HARDWARE-001"
    assert [entry["name"] for entry in manifest["files"]] == sorted(
        name for name in EVIDENCE_FILES if name != "EVIDENCE_MANIFEST.json"
    )


def test_prepare_manifest_rejects_empty_evidence(tmp_path: Path) -> None:
    run = write_run(tmp_path, empty=("serial.log",))

    with pytest.raises(ValueError, match="empty evidence files: serial.log"):
        prepare_manifest(run)


def test_prepare_manifest_rejects_missing_identity(tmp_path: Path) -> None:
    run = write_run(tmp_path, identity={"receiver": ""})

    with pytest.raises(ValueError, match="missing identity metadata: receiver"):
        prepare_manifest(run)

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.finalize_hardware_qualification_run import validate_evidence_manifest


def write_manifest(run_dir: Path, files: list[str]) -> None:
    entries = []
    for name in files:
        data = (run_dir / name).read_bytes()
        entries.append({
            "name": name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    (run_dir / "EVIDENCE_MANIFEST.json").write_text(
        json.dumps({"schema": 1, "files": entries}, indent=2) + "\n",
        encoding="utf-8",
    )


def test_validate_evidence_manifest_accepts_matching_hashes(tmp_path: Path) -> None:
    (tmp_path / "serial.log").write_text("$GNGGA,valid\n", encoding="utf-8")
    write_manifest(tmp_path, ["serial.log"])

    validate_evidence_manifest(tmp_path)


def test_validate_evidence_manifest_rejects_tampering(tmp_path: Path) -> None:
    (tmp_path / "serial.log").write_text("original\n", encoding="utf-8")
    write_manifest(tmp_path, ["serial.log"])
    (tmp_path / "serial.log").write_text("tampered\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="SHA-256 mismatch"):
        validate_evidence_manifest(tmp_path)


def test_validate_evidence_manifest_rejects_missing_file(tmp_path: Path) -> None:
    (tmp_path / "serial.log").write_text("captured\n", encoding="utf-8")
    write_manifest(tmp_path, ["serial.log"])
    (tmp_path / "serial.log").unlink()

    with pytest.raises(SystemExit, match="evidence file does not exist"):
        validate_evidence_manifest(tmp_path)

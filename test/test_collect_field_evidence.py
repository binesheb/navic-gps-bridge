from __future__ import annotations

import json
from pathlib import Path

from tools.collect_field_evidence import main
from tools.verify_evidence_manifest import verify


def test_collect_uses_canonical_manifest_and_identity(tmp_path: Path):
    source = tmp_path / "capture.log"
    source.write_text("$GPGGA,field\n", encoding="utf-8")
    output = tmp_path / "run"

    assert main([
        str(output),
        "--file", f"serial.log={source}",
        "--device", "bridge-01",
        "--firmware-commit", "abc123",
        "--receiver", "GNSS-01",
        "--test-id", "H01",
    ]) == 0

    manifest = json.loads((output / "EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == 1
    assert manifest["device"] == "bridge-01"
    assert manifest["firmware_commit"] == "abc123"
    assert manifest["receiver"] == "GNSS-01"
    assert manifest["test_id"] == "H01"
    assert manifest["files"][0]["name"] == "serial.log"
    assert verify(output / "EVIDENCE_MANIFEST.json")["passed"] is True


def test_collect_rejects_empty_identity(tmp_path: Path):
    source = tmp_path / "capture.log"
    source.write_text("capture\n", encoding="utf-8")
    output = tmp_path / "run"

    try:
        main([
            str(output),
            "--file", f"serial.log={source}",
            "--device", "",
            "--firmware-commit", "abc123",
            "--receiver", "GNSS-01",
            "--test-id", "H01",
        ])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected argparse failure for empty identity")

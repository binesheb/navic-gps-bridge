from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.generate_evidence_manifest import build_manifest


def test_build_manifest_hashes_sorted_files(tmp_path: Path):
    (tmp_path / "z.log").write_text("zulu\n", encoding="utf-8")
    (tmp_path / "a.json").write_text('{"ok":true}\n', encoding="utf-8")

    manifest = build_manifest(
        tmp_path,
        ["z.log", "a.json", "a.json"],
        device="bridge-01",
        firmware_commit="abc123",
        receiver="GNSS-01",
        test_id="H01",
    )

    assert manifest["schema"] == 1
    assert manifest["device"] == "bridge-01"
    assert [entry["name"] for entry in manifest["files"]] == ["a.json", "z.log"]
    assert manifest["files"][0]["bytes"] == (tmp_path / "a.json").stat().st_size
    assert manifest["files"][0]["sha256"] == hashlib.sha256((tmp_path / "a.json").read_bytes()).hexdigest()


def test_build_manifest_rejects_missing_file(tmp_path: Path):
    with pytest.raises(ValueError, match="does not exist"):
        build_manifest(
            tmp_path,
            ["missing.log"],
            device="bridge-01",
            firmware_commit="abc123",
            receiver="GNSS-01",
            test_id="H01",
        )


def test_build_manifest_rejects_path_traversal(tmp_path: Path):
    with pytest.raises(ValueError, match="simple filenames"):
        build_manifest(
            tmp_path,
            ["../outside.log"],
            device="bridge-01",
            firmware_commit="abc123",
            receiver="GNSS-01",
            test_id="H01",
        )


def test_generated_manifest_is_accepted_by_verifier(tmp_path: Path):
    (tmp_path / "live.csv").write_text("time,nmea\n0,$GPGGA\n", encoding="utf-8")
    manifest = build_manifest(
        tmp_path,
        ["live.csv"],
        device="bridge-01",
        firmware_commit="abc123",
        receiver="GNSS-01",
        test_id="H01",
    )
    manifest_path = tmp_path / "EVIDENCE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    from tools.verify_evidence_manifest import verify

    result = verify(manifest_path)
    assert result["passed"] is True
    assert result["files_verified"] == 1

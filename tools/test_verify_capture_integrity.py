#!/usr/bin/env python3
"""Regression tests for verify_capture_integrity.py."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import verify_capture_integrity


REQUIRED = {
    "live.csv": b"timestamp,lat,lon\n1,10,20\n",
    "nmea.log": b"$GNGGA,1\n",
    "nmea_timeline.log": b"1 -> GNGGA\n",
}


def write_valid_run(root: Path) -> None:
    files = []
    for name, data in REQUIRED.items():
        path = root / name
        path.write_bytes(data)
        files.append({
            "name": name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    (root / "CAPTURE.json").write_text(json.dumps({
        "capture": {"schema": 1},
        "evidence_integrity": {
            "schema": 1,
            "hash_algorithm": "SHA-256",
            "self_excluded": True,
            "files": files,
        },
    }), encoding="utf-8")


class VerifyCaptureIntegrityTests(unittest.TestCase):
    def test_valid_bundle_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_run(root)
            result = verify_capture_integrity.verify(root)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["checked_files"], 3)
            self.assertEqual(result["mismatches"], [])

    def test_modified_artifact_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_run(root)
            (root / "nmea.log").write_text("tampered\n", encoding="utf-8")
            result = verify_capture_integrity.verify(root)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["mismatches"], [{"name": "nmea.log", "reason": "hash_or_size_mismatch"}])

    def test_missing_required_entry_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_run(root)
            report = json.loads((root / "CAPTURE.json").read_text(encoding="utf-8"))
            report["evidence_integrity"]["files"] = report["evidence_integrity"]["files"][:-1]
            (root / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "omits required evidence"):
                verify_capture_integrity.verify(root)

    def test_duplicate_entry_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_run(root)
            report = json.loads((root / "CAPTURE.json").read_text(encoding="utf-8"))
            report["evidence_integrity"]["files"].append(report["evidence_integrity"]["files"][0])
            (root / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate evidence entry"):
                verify_capture_integrity.verify(root)

    def test_path_traversal_entry_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_run(root)
            report = json.loads((root / "CAPTURE.json").read_text(encoding="utf-8"))
            report["evidence_integrity"]["files"][0]["name"] = "../live.csv"
            (root / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "single path component"):
                verify_capture_integrity.verify(root)

    def test_symlink_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_run(root)
            target = root / "real-nmea.log"
            target.write_bytes(REQUIRED["nmea.log"])
            (root / "nmea.log").unlink()
            (root / "nmea.log").symlink_to(target)
            result = verify_capture_integrity.verify(root)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["mismatches"], [{"name": "nmea.log", "reason": "missing_or_symlink"}])

    def test_unsupported_entry_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_run(root)
            report = json.loads((root / "CAPTURE.json").read_text(encoding="utf-8"))
            report["evidence_integrity"]["files"].append({
                "name": "unexpected.bin", "bytes": 0, "sha256": "0" * 64,
            })
            (root / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported evidence entry"):
                verify_capture_integrity.verify(root)

    def test_self_file_entry_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_run(root)
            report = json.loads((root / "CAPTURE.json").read_text(encoding="utf-8"))
            report["evidence_integrity"]["files"].append({
                "name": "CAPTURE.json", "bytes": 0, "sha256": "0" * 64,
            })
            (root / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported evidence entry"):
                verify_capture_integrity.verify(root)

    def test_invalid_hash_metadata_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_run(root)
            report = json.loads((root / "CAPTURE.json").read_text(encoding="utf-8"))
            report["evidence_integrity"]["files"][0]["sha256"] = "not-a-hash"
            (root / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid SHA-256 value"):
                verify_capture_integrity.verify(root)

    def test_boolean_byte_count_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_run(root)
            report = json.loads((root / "CAPTURE.json").read_text(encoding="utf-8"))
            report["evidence_integrity"]["files"][0]["bytes"] = True
            (root / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid byte count"):
                verify_capture_integrity.verify(root)


if __name__ == "__main__":
    unittest.main()

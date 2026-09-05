from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import verify_field_evidence


class VerifyFieldEvidenceTests(unittest.TestCase):
    def make_bundle(self, files: dict[str, bytes]) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        bundle = Path(temp.name)
        entries = []
        for name, content in files.items():
            path = bundle / name
            path.write_bytes(content)
            entries.append({
                "name": name,
                "bytes": len(content),
                "sha256": verify_field_evidence.sha256(path),
            })
        (bundle / "EVIDENCE_MANIFEST.json").write_text(
            json.dumps({"schema": 1, "files": entries}) + "\n", encoding="utf-8"
        )
        return temp, bundle

    def test_valid_bundle(self) -> None:
        temp, bundle = self.make_bundle({"nmea.txt": b"$GPRMC,test\n", "live.json": b"{}\n"})
        self.addCleanup(temp.cleanup)
        self.assertEqual(verify_field_evidence.main.__name__, "main")
        with mock.patch("sys.argv", ["verify_field_evidence.py", str(bundle)]):
            self.assertEqual(verify_field_evidence.main(), 0)

    def test_missing_file_fails(self) -> None:
        temp, bundle = self.make_bundle({"nmea.txt": b"capture"})
        self.addCleanup(temp.cleanup)
        (bundle / "nmea.txt").unlink()
        with mock.patch("sys.argv", ["verify_field_evidence.py", str(bundle)]):
            self.assertEqual(verify_field_evidence.main(), 1)

    def test_tampered_file_fails(self) -> None:
        temp, bundle = self.make_bundle({"nmea.txt": b"capture"})
        self.addCleanup(temp.cleanup)
        (bundle / "nmea.txt").write_bytes(b"tampered")
        with mock.patch("sys.argv", ["verify_field_evidence.py", str(bundle)]):
            self.assertEqual(verify_field_evidence.main(), 1)

    def test_duplicate_manifest_entry_fails(self) -> None:
        temp, bundle = self.make_bundle({"nmea.txt": b"capture"})
        self.addCleanup(temp.cleanup)
        manifest_path = bundle / "EVIDENCE_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"].append(manifest["files"][0])
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with mock.patch("sys.argv", ["verify_field_evidence.py", str(bundle)]):
            self.assertEqual(verify_field_evidence.main(), 1)

    def test_path_traversal_entry_fails(self) -> None:
        temp, bundle = self.make_bundle({"nmea.txt": b"capture"})
        self.addCleanup(temp.cleanup)
        manifest_path = bundle / "EVIDENCE_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"][0]["name"] = "../nmea.txt"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with mock.patch("sys.argv", ["verify_field_evidence.py", str(bundle)]):
            self.assertEqual(verify_field_evidence.main(), 1)


if __name__ == "__main__":
    unittest.main()

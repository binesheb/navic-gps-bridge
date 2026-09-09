from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_field_evidence import verify_bundle


class VerifyFieldEvidenceTests(unittest.TestCase):
    def _bundle(self, payload: bytes = b"NMEA evidence\n") -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        bundle = Path(temp.name)
        evidence = bundle / "nmea.log"
        evidence.write_bytes(payload)
        manifest = {
            "schema": 1,
            "files": [{
                "name": "nmea.log",
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }],
        }
        (bundle / "EVIDENCE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        return temp, bundle

    def test_valid_bundle_passes(self) -> None:
        temp, bundle = self._bundle()
        self.addCleanup(temp.cleanup)
        self.assertEqual(verify_bundle(bundle), [])

    def test_modified_evidence_is_rejected(self) -> None:
        temp, bundle = self._bundle()
        self.addCleanup(temp.cleanup)
        (bundle / "nmea.log").write_bytes(b"tampered\n")
        failures = verify_bundle(bundle)
        self.assertTrue(any("SHA-256 mismatch" in item for item in failures))

    def test_missing_evidence_is_rejected(self) -> None:
        temp, bundle = self._bundle()
        self.addCleanup(temp.cleanup)
        (bundle / "nmea.log").unlink()
        failures = verify_bundle(bundle)
        self.assertIn("missing evidence file: nmea.log", failures)

    def test_path_traversal_entry_is_rejected(self) -> None:
        temp, bundle = self._bundle()
        self.addCleanup(temp.cleanup)
        manifest = {
            "schema": 1,
            "files": [{"name": "../outside.log", "bytes": 0, "sha256": "0" * 64}],
        }
        (bundle / "EVIDENCE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        failures = verify_bundle(bundle)
        self.assertTrue(any("invalid evidence filename" in item for item in failures))


if __name__ == "__main__":
    unittest.main()

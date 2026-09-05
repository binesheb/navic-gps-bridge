#!/usr/bin/env python3
"""Regression tests for qualify_field_evidence.py."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from qualify_field_evidence import qualify


class QualificationTests(unittest.TestCase):
    def make_bundle(self, nmea=True, live=True, commit="abc123"):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        files = []
        for name, passed in (("nmea-verdict.json", nmea), ("live-verdict.json", live)):
            path = root / name
            path.write_text(json.dumps({"passed": passed}) + "\n", encoding="utf-8")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            files.append({"name": name, "bytes": path.stat().st_size, "sha256": digest})
        (root / "EVIDENCE_MANIFEST.json").write_text(
            json.dumps({"schema": 1, "firmware_commit": commit, "files": files}),
            encoding="utf-8",
        )
        return temp, root

    def test_passes_complete_verified_bundle(self):
        temp, root = self.make_bundle()
        self.addCleanup(temp.cleanup)
        report, failures = qualify(str(root), expected_commit="abc123")
        self.assertEqual([], failures)
        self.assertTrue(report["passed"])
        self.assertTrue(report["integrity_verified"])

    def test_rejects_failed_verdict(self):
        temp, root = self.make_bundle(nmea=False)
        self.addCleanup(temp.cleanup)
        report, failures = qualify(str(root), expected_commit="abc123")
        self.assertFalse(report["passed"])
        self.assertTrue(any("nmea-verdict.json" in failure for failure in failures))

    def test_rejects_commit_mismatch(self):
        temp, root = self.make_bundle()
        self.addCleanup(temp.cleanup)
        report, failures = qualify(str(root), expected_commit="different")
        self.assertFalse(report["passed"])
        self.assertTrue(any("firmware commit" in failure for failure in failures))

    def test_rejects_missing_manifest_entry(self):
        temp, root = self.make_bundle()
        self.addCleanup(temp.cleanup)
        manifest = json.loads((root / "EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
        manifest["files"] = [manifest["files"][0]]
        (root / "EVIDENCE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        report, failures = qualify(str(root))
        self.assertFalse(report["passed"])
        self.assertTrue(any("does not include required verdict" in failure for failure in failures))

    def test_rejects_tampered_verdict(self):
        temp, root = self.make_bundle()
        self.addCleanup(temp.cleanup)
        (root / "nmea-verdict.json").write_text(json.dumps({"passed": False}) + "\n", encoding="utf-8")
        report, failures = qualify(str(root), expected_commit="abc123")
        self.assertFalse(report["passed"])
        self.assertFalse(report["integrity_verified"])
        self.assertTrue(any("SHA-256 mismatch" in failure for failure in failures))

    def test_rejects_unsupported_schema(self):
        temp, root = self.make_bundle()
        self.addCleanup(temp.cleanup)
        manifest = json.loads((root / "EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
        manifest["schema"] = 2
        (root / "EVIDENCE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        report, failures = qualify(str(root))
        self.assertFalse(report["passed"])
        self.assertTrue(any("unsupported manifest schema" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()

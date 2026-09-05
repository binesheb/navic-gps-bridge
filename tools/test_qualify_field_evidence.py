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
    def make_bundle(self, nmea=True, live=True, health_sequence=None, commit="abc123"):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        files = []
        verdicts = [("nmea-verdict.json", nmea), ("live-verdict.json", live)]
        if health_sequence is not None:
            verdicts.append(("health-sequence.json", health_sequence))
        for name, passed in verdicts:
            path = root / name
            value = {"passed": passed}
            if name == "health-sequence.json":
                value["qualification_ready"] = passed
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
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
        self.assertIsNone(report["health_sequence_passed"])

    def test_passes_when_physical_recovery_verdict_is_required_and_valid(self):
        temp, root = self.make_bundle(health_sequence=True)
        self.addCleanup(temp.cleanup)
        report, failures = qualify(
            str(root), expected_commit="abc123", health_sequence_name="health-sequence.json"
        )
        self.assertEqual([], failures)
        self.assertTrue(report["passed"])
        self.assertTrue(report["health_sequence_passed"])

    def test_rejects_failed_verdict(self):
        temp, root = self.make_bundle(nmea=False)
        self.addCleanup(temp.cleanup)
        report, failures = qualify(str(root), expected_commit="abc123")
        self.assertFalse(report["passed"])
        self.assertTrue(any("nmea-verdict.json" in failure for failure in failures))

    def test_rejects_physical_recovery_verdict_not_ready(self):
        temp, root = self.make_bundle(health_sequence=False)
        self.addCleanup(temp.cleanup)
        report, failures = qualify(
            str(root), expected_commit="abc123", health_sequence_name="health-sequence.json"
        )
        self.assertFalse(report["passed"])
        self.assertFalse(report["health_sequence_passed"])
        self.assertTrue(any("qualification_ready=true" in failure for failure in failures))

    def test_rejects_missing_physical_recovery_verdict(self):
        temp, root = self.make_bundle()
        self.addCleanup(temp.cleanup)
        report, failures = qualify(
            str(root), expected_commit="abc123", health_sequence_name="health-sequence.json"
        )
        self.assertFalse(report["passed"])
        self.assertTrue(any("required health-sequence verdict" in failure for failure in failures))

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
        (root / "nmea-verdict.json").write_text(json.dumps({"passed": None}) + "\n", encoding="utf-8")
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

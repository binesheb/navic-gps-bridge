import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from verify_recovery_report import verify


class VerifyRecoveryReportTests(unittest.TestCase):
    def make_bundle(self):
        root = Path(tempfile.mkdtemp())
        files = {
            "CAPTURE.json": b'{"schema_version":2}\n',
            "live.csv": b'elapsed_s,health\n0,HEALTHY\n',
            "nmea_timeline.log": b'0.0 CONNECT\n',
        }
        for name, content in files.items():
            (root / name).write_bytes(content)
        report = {
            "schema_version": 1,
            "qualification_ready": True,
            "evidence_sha256": {
                name: hashlib.sha256(content).hexdigest() for name, content in files.items()
            },
        }
        report_path = root / "qualification.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        return root, report_path

    def test_valid_bundle_matches_report(self):
        root, report = self.make_bundle()
        result = verify(report, root)
        self.assertTrue(result["passed"])
        self.assertTrue(all(item["match"] for item in result["evidence"].values()))

    def test_tampered_evidence_fails(self):
        root, report = self.make_bundle()
        (root / "live.csv").write_bytes(b"tampered\n")
        result = verify(report, root)
        self.assertFalse(result["passed"])
        self.assertFalse(result["evidence"]["live.csv"]["match"])

    def test_missing_fingerprints_are_rejected(self):
        root, report = self.make_bundle()
        report.write_text(json.dumps({"schema_version": 1, "qualification_ready": True}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing evidence_sha256"):
            verify(report, root)

    def test_unqualified_report_is_rejected(self):
        root, report = self.make_bundle()
        data = json.loads(report.read_text(encoding="utf-8"))
        data["qualification_ready"] = False
        report.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "qualification_ready=true"):
            verify(report, root)

    def test_invalid_digest_is_rejected(self):
        root, report = self.make_bundle()
        data = json.loads(report.read_text(encoding="utf-8"))
        data["evidence_sha256"]["live.csv"] = "not-a-digest"
        report.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
            verify(report, root)


if __name__ == "__main__":
    unittest.main()

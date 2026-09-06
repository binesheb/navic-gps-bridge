#!/usr/bin/env python3
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from run_field_qualification import run


LIVE = """elapsed_s,status
0,HEALTHY
1,STALE
2,RECOVERING
3,HEALTHY
"""
TIMELINE = """1000.0\t0.0\tCONNECT\tport=10110
1001.0\t1.0\tDISCONNECT\tpeer_closed
1001.5\t1.5\tCONNECT\tport=10110
1002.0\t2.0\tNMEA\t$GNRMC,example
"""


class FieldQualificationRunnerTests(unittest.TestCase):
    def make_bundle(self, root: Path):
        bundle = root / "bundle"
        bundle.mkdir()
        (bundle / "live.csv").write_text(LIVE, encoding="utf-8")
        (bundle / "nmea_timeline.log").write_text(TIMELINE, encoding="utf-8")
        (bundle / "nmea-verdict.json").write_text("{\"passed\":true}\n", encoding="utf-8")
        (bundle / "serial.log").write_text("boot\nrecovered\n", encoding="utf-8")
        capture = {
            "schema_version": 2,
            "duration_s": 5.0,
            "nmea_timeline": "nmea_timeline.log",
            "simultaneous_window": True,
            "http_errors": 0,
            "nmea_sentences": 1,
            "nmea_reconnects": 1,
        }
        (bundle / "CAPTURE.json").write_text(json.dumps(capture), encoding="utf-8")
        files = []
        for name in ("nmea-verdict.json", "live.csv", "serial.log", "nmea_timeline.log", "CAPTURE.json"):
            path = bundle / name
            files.append({
                "name": name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
        manifest = {
            "schema": 1,
            "firmware_commit": "abc123",
            "device": "bridge-01",
            "receiver": "GNSS-test",
            "test_id": "recovery-001",
            "files": files,
        }
        (bundle / "EVIDENCE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        return bundle

    def test_runs_complete_pipeline(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = self.make_bundle(root)
            output = root / "output"
            result = run(bundle, output)
            self.assertTrue(result["passed"])
            self.assertTrue(result["preflight"]["identity_complete"])
            self.assertTrue(result["manifest_verification"]["passed"])
            self.assertTrue(result["qualification"]["qualification_ready"])
            self.assertTrue(result["recovery_verification"]["passed"])
            self.assertTrue((output / "FIELD_QUALIFICATION.md").is_file())
            report = (output / "FIELD_QUALIFICATION.md").read_text(encoding="utf-8")
            self.assertIn("bridge-01", report)
            self.assertIn("recovery-001", report)

    def test_tampered_bundle_stops_before_qualification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = self.make_bundle(root)
            (bundle / "live.csv").write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest verification"):
                run(bundle, root / "output")


if __name__ == "__main__":
    unittest.main()

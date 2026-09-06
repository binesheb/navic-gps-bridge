import json
import tempfile
import unittest
from pathlib import Path

from qualify_recovery_bundle import validate_bundle


LIVE = """elapsed_s,status\n0,HEALTHY\n1,STALE\n2,RECOVERING\n3,HEALTHY\n"""
TIMELINE = """1000.0\t0.0\tCONNECT\tport=10110\n1001.0\t1.0\tDISCONNECT\tpeer_closed\n1001.5\t1.5\tCONNECT\tport=10110\n1002.0\t2.0\tNMEA\t$GNRMC,example\n"""


class RecoveryBundleTests(unittest.TestCase):
    def write_bundle(self, capture=None):
        root = Path(tempfile.mkdtemp())
        (root / "live.csv").write_text(LIVE, encoding="utf-8")
        (root / "nmea_timeline.log").write_text(TIMELINE, encoding="utf-8")
        metadata = capture or {
            "schema_version": 2,
            "duration_s": 5.0,
            "nmea_timeline": "nmea_timeline.log",
            "simultaneous_window": True,
            "http_errors": 0,
            "nmea_sentences": 1,
            "nmea_reconnects": 1,
        }
        (root / "CAPTURE.json").write_text(json.dumps(metadata), encoding="utf-8")
        return root

    def test_valid_bundle_qualifies(self):
        report = validate_bundle(self.write_bundle())
        self.assertTrue(report["bundle_integrity"])
        self.assertTrue(report["qualification_ready"])
        self.assertTrue(report["simultaneous_window"])

    def test_rejects_non_simultaneous_capture(self):
        root = self.write_bundle({
            "schema_version": 2,
            "duration_s": 5.0,
            "nmea_timeline": "nmea_timeline.log",
            "simultaneous_window": False,
        })
        with self.assertRaisesRegex(ValueError, "simultaneous_window"):
            validate_bundle(root)

    def test_rejects_wrong_timeline_reference(self):
        root = self.write_bundle({
            "schema_version": 2,
            "duration_s": 5.0,
            "nmea_timeline": "other.log",
            "simultaneous_window": True,
        })
        with self.assertRaisesRegex(ValueError, "reference"):
            validate_bundle(root)

    def test_rejects_missing_live_file(self):
        root = self.write_bundle()
        (root / "live.csv").unlink()
        with self.assertRaisesRegex(ValueError, "live.csv"):
            validate_bundle(root)

    def test_rejects_invalid_capture_duration(self):
        root = self.write_bundle({
            "schema_version": 2,
            "duration_s": "5",
            "nmea_timeline": "nmea_timeline.log",
            "simultaneous_window": True,
        })
        with self.assertRaisesRegex(ValueError, "duration_s"):
            validate_bundle(root)


if __name__ == "__main__":
    unittest.main()

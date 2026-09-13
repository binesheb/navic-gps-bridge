import json
import tempfile
import unittest
from pathlib import Path

import validate_field_capture


class ValidateFieldCaptureTests(unittest.TestCase):
    def _write_run(self, report=None, empty=()):
        root = Path(tempfile.mkdtemp())
        payload = report or {
            "schema_version": 2,
            "simultaneous_window": True,
            "duration_s": 60,
            "interval_s": 1,
            "live_samples": 60,
            "nmea_sentences": 120,
            "nmea_connections": 1,
            "nmea_timeline_records": 121,
            "nmea_timeline": "nmea_timeline.log",
            "nmea_port": 10110,
        }
        (root / "CAPTURE.json").write_text(json.dumps(payload), encoding="utf-8")
        (root / "live.csv").write_text("timestamp,lat,lon\n" + "2026-09-13T00:00:00Z,10.0,76.0\n" * 60, encoding="utf-8")
        (root / "nmea.log").write_text("$GPGGA,1\n" * 120, encoding="utf-8")
        (root / "nmea_timeline.log").write_text("timeline\n" * 121, encoding="utf-8")
        for name in empty:
            (root / name).write_text("", encoding="utf-8")
        return root

    def test_accepts_valid_capture(self):
        report = validate_field_capture.validate_capture(self._write_run())
        self.assertEqual(report["live_samples"], 60)

    def test_rejects_non_simultaneous_capture(self):
        root = self._write_run({
            "schema_version": 2,
            "simultaneous_window": False,
            "duration_s": 60,
            "interval_s": 1,
            "live_samples": 1,
            "nmea_sentences": 1,
            "nmea_connections": 1,
            "nmea_timeline_records": 1,
            "nmea_port": 10110,
        })
        with self.assertRaisesRegex(ValueError, "simultaneous"):
            validate_field_capture.validate_capture(root)

    def test_rejects_missing_artifact(self):
        root = self._write_run()
        (root / "nmea.log").unlink()
        with self.assertRaisesRegex(ValueError, "missing capture artifacts"):
            validate_field_capture.validate_capture(root)

    def test_rejects_empty_artifact(self):
        root = self._write_run(empty=("live.csv",))
        with self.assertRaisesRegex(ValueError, "empty capture artifacts"):
            validate_field_capture.validate_capture(root)

    def test_rejects_zero_observations(self):
        root = self._write_run()
        payload = json.loads((root / "CAPTURE.json").read_text())
        payload["live_samples"] = 0
        (root / "CAPTURE.json").write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "live_samples"):
            validate_field_capture.validate_capture(root)


if __name__ == "__main__":
    unittest.main()

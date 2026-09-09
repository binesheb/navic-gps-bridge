import csv
import json
import tempfile
import unittest
from pathlib import Path

import validate_capture_integrity


class ValidateCaptureIntegrityTests(unittest.TestCase):
    def _run(self, live_rows=2, nmea_rows=3, timeline_rows=4):
        root = Path(tempfile.mkdtemp())
        report = {
            "schema_version": 2,
            "simultaneous_window": True,
            "duration_s": 10,
            "interval_s": 1,
            "live_samples": live_rows,
            "nmea_sentences": nmea_rows,
            "nmea_connections": 1,
            "nmea_timeline_records": timeline_rows,
            "nmea_port": 10110,
        }
        (root / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
        with (root / "live.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=validate_capture_integrity.LIVE_FIELDS)
            writer.writeheader()
            for i in range(live_rows):
                writer.writerow({key: str(i) for key in validate_capture_integrity.LIVE_FIELDS})
        (root / "nmea.log").write_text("".join(f"$GPRMC,{i}*00\n" for i in range(nmea_rows)), encoding="utf-8")
        (root / "nmea_timeline.log").write_text("".join(f"{i}.000\t{i}.000\tNMEA\t$GPRMC\n" for i in range(timeline_rows)), encoding="utf-8")
        return root

    def test_accepts_matching_counts(self):
        result = validate_capture_integrity.validate_integrity(self._run())
        self.assertTrue(result["valid"])
        self.assertEqual(result["counts"]["nmea_sentences"], 3)

    def test_rejects_metadata_count_mismatch(self):
        root = self._run()
        report = json.loads((root / "CAPTURE.json").read_text())
        report["nmea_sentences"] = 99
        (root / "CAPTURE.json").write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "nmea_sentences"):
            validate_capture_integrity.validate_integrity(root)

    def test_rejects_live_header_mismatch(self):
        root = self._run()
        (root / "live.csv").write_text("wrong,header\n1,2\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "live.csv header"):
            validate_capture_integrity.validate_integrity(root)


if __name__ == "__main__":
    unittest.main()

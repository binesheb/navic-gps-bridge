import csv
import json
import tempfile
import unittest
from pathlib import Path

import validate_capture_integrity
import validate_capture_timing


class ValidateCaptureTimingTests(unittest.TestCase):
    def _run(self, live_times=(0.0, 1.0), timeline_times=(0.0, 0.5, 1.0)):
        root = Path(tempfile.mkdtemp())
        report = {
            "schema_version": 2,
            "simultaneous_window": True,
            "duration_s": 10,
            "interval_s": 1,
            "live_samples": len(live_times),
            "nmea_sentences": len(timeline_times),
            "nmea_connections": 1,
            "nmea_timeline_records": len(timeline_times),
            "nmea_port": 10110,
        }
        (root / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
        with (root / "live.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=validate_capture_integrity.LIVE_FIELDS)
            writer.writeheader()
            for i, value in enumerate(live_times):
                writer.writerow({key: str(i) if key != "elapsed_s" else str(value) for key in writer.fieldnames})
        (root / "nmea.log").write_text("".join(f"$GPRMC,{i}*00\n" for i in range(len(timeline_times))), encoding="utf-8")
        (root / "nmea_timeline.log").write_text(
            "".join(f"{value:.3f}\t{value:.3f}\tNMEA\t$GPRMC\n" for value in timeline_times), encoding="utf-8"
        )
        return root

    def test_accepts_monotonic_timing(self):
        result = validate_capture_timing.validate_timing(self._run())
        self.assertTrue(result["valid"])
        self.assertEqual(result["duration_s"], 10.0)
        self.assertEqual(result["live_last_elapsed_s"], 1.0)

    def test_rejects_non_monotonic_live_timing(self):
        with self.assertRaisesRegex(ValueError, "live.csv elapsed time is not monotonic"):
            validate_capture_timing.validate_timing(self._run(live_times=(0.0, 2.0, 1.0)))

    def test_rejects_timeline_outside_duration(self):
        root = self._run(timeline_times=(0.0, 11.0))
        report = json.loads((root / "CAPTURE.json").read_text())
        report["nmea_timeline_records"] = 2
        (root / "CAPTURE.json").write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "outside capture duration"):
            validate_capture_timing.validate_timing(root)


if __name__ == "__main__":
    unittest.main()

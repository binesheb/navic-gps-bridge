import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import live_capture


class LiveCaptureTests(unittest.TestCase):
    def test_flatten_preserves_status_core_and_nested_diagnostics(self):
        row = live_capture._flatten({
            "status": "STALE",
            "data_available": True,
            "data_fresh": False,
            "data_age_ms": 4200,
            "fix": True,
            "latitude": 10.1,
            "longitude": 76.2,
            "satellites": 8,
            "gnss_health": {
                "receiver_online": True,
                "stale": True,
                "accepted_sentences": 120,
            },
            "gnss_recovery": {
                "monitoring": True,
                "recovering": False,
                "attempts": 2,
            },
        })
        self.assertEqual(row["status"], "STALE")
        self.assertTrue(row["data_available"])
        self.assertFalse(row["data_fresh"])
        self.assertEqual(row["data_age_ms"], 4200)
        self.assertTrue(row["gnss_receiver_online"])
        self.assertTrue(row["gnss_stale"])
        self.assertEqual(row["gnss_accepted_sentences"], 120)
        self.assertTrue(row["recovery_monitoring"])
        self.assertEqual(row["recovery_attempts"], 2)

    @patch("live_capture.fetch_live")
    def test_capture_writes_samples_and_request_failures(self, fetch_live):
        fetch_live.side_effect = [
            (200, {"status": "HEALTHY", "data_available": True, "fix": True, "packets": 1}),
            OSError("bridge unavailable"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capture.csv"
            samples, failures = live_capture.capture(
                "http://bridge", str(output), interval=0.001, duration=0.001, timeout=1
            )
            self.assertGreaterEqual(samples, 1)
            self.assertEqual(failures, 0)
            with output.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]["http_ok"], "True")
            self.assertEqual(rows[0]["status"], "HEALTHY")
            self.assertEqual(rows[0]["data_available"], "True")

    @patch("live_capture.fetch_live")
    @patch("live_capture.time.sleep")
    @patch("live_capture.time.monotonic", side_effect=[0.0, 0.0, 1.0])
    def test_bounded_capture_records_sample_at_or_after_duration(self, monotonic, sleep, fetch_live):
        fetch_live.return_value = (200, {"status": "HEALTHY", "data_available": True, "fix": True, "packets": 1})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capture.csv"
            samples, failures = live_capture.capture(
                "http://bridge", str(output), interval=0.1, duration=0.5, timeout=1
            )
            self.assertEqual(samples, 1)
            self.assertEqual(failures, 0)
            with output.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertGreaterEqual(float(rows[-1]["elapsed_s"]), 0.5)
            sleep.assert_not_called()

    def test_invalid_capture_arguments_are_rejected(self):
        with self.assertRaises(SystemExit):
            live_capture.main(["http://bridge", "out.csv", "--interval", "0"])


if __name__ == "__main__":
    unittest.main()

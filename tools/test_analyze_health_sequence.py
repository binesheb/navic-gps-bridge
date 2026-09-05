import csv
import tempfile
import unittest
from pathlib import Path

from analyze_health_sequence import analyze


class HealthSequenceTests(unittest.TestCase):
    def write_csv(self, rows):
        handle = tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", delete=False)
        with handle:
            writer = csv.DictWriter(handle, fieldnames=["elapsed_s", "status"])
            writer.writeheader()
            for elapsed, status in rows:
                writer.writerow({"elapsed_s": elapsed, "status": status})
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return handle.name

    def test_recovery_sequence_is_detected_and_timed(self):
        report = analyze(self.write_csv([
            (0, "HEALTHY"), (1, "HEALTHY"), (3, "STALE"),
            (4, "RECOVERING"), (5, "RECOVERING"), (7, "HEALTHY")
        ]))
        self.assertEqual(report["transitions"], ["HEALTHY", "STALE", "RECOVERING", "HEALTHY"])
        self.assertTrue(report["recovery_sequence_observed"])
        self.assertEqual(report["recovery_duration_s"], 3.0)
        self.assertTrue(report["capture_integrity_valid"])
        self.assertTrue(report["qualification_ready"])

    def test_recovery_duration_limit_can_block_qualification(self):
        report = analyze(self.write_csv([
            (0, "HEALTHY"), (2, "STALE"), (3, "RECOVERING"), (10, "HEALTHY")
        ]), max_recovery_seconds=5)
        self.assertTrue(report["recovery_sequence_observed"])
        self.assertEqual(report["recovery_duration_s"], 7.0)
        self.assertFalse(report["recovery_duration_within_limit"])
        self.assertFalse(report["qualification_ready"])

    def test_missing_recovery_does_not_qualify(self):
        report = analyze(self.write_csv([
            (0, "HEALTHY"), (1, "STALE"), (2, "NO_FIX"), (3, "HEALTHY")
        ]))
        self.assertFalse(report["recovery_sequence_observed"])
        self.assertFalse(report["qualification_ready"])

    def test_empty_rows_are_ignored(self):
        report = analyze(self.write_csv([
            (0, ""), (1, "HEALTHY"), (2, ""), (3, "STALE")
        ]))
        self.assertEqual(report["non_empty_samples"], 2)
        self.assertEqual(report["transitions"], ["HEALTHY", "STALE"])

    def test_backwards_elapsed_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "elapsed_s moved backwards"):
            analyze(self.write_csv([
                (0, "HEALTHY"), (2, "STALE"), (1, "RECOVERING")
            ]))


if __name__ == "__main__":
    unittest.main()

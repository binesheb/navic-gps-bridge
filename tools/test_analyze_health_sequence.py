import csv
import tempfile
import unittest
from pathlib import Path

from analyze_health_sequence import analyze


class HealthSequenceTests(unittest.TestCase):
    def write_csv(self, statuses):
        handle = tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", delete=False)
        with handle:
            writer = csv.DictWriter(handle, fieldnames=["elapsed_s", "status"])
            writer.writeheader()
            for index, status in enumerate(statuses):
                writer.writerow({"elapsed_s": index, "status": status})
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return handle.name

    def test_recovery_sequence_is_detected(self):
        report = analyze(self.write_csv(["HEALTHY", "HEALTHY", "STALE", "RECOVERING", "RECOVERING", "HEALTHY"]))
        self.assertEqual(report["transitions"], ["HEALTHY", "STALE", "RECOVERING", "HEALTHY"])
        self.assertTrue(report["recovery_sequence_observed"])
        self.assertTrue(report["qualification_ready"])

    def test_missing_recovery_does_not_qualify(self):
        report = analyze(self.write_csv(["HEALTHY", "STALE", "NO_FIX", "HEALTHY"]))
        self.assertFalse(report["recovery_sequence_observed"])
        self.assertFalse(report["qualification_ready"])

    def test_empty_rows_are_ignored(self):
        report = analyze(self.write_csv(["", "HEALTHY", "", "STALE"]))
        self.assertEqual(report["non_empty_samples"], 2)
        self.assertEqual(report["transitions"], ["HEALTHY", "STALE"])


if __name__ == "__main__":
    unittest.main()

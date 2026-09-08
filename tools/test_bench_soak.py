import unittest
from unittest.mock import patch

from bench_soak import run


class BenchSoakTests(unittest.TestCase):
    def test_all_samples_must_pass_and_record_timestamps(self):
        live = {"fix": True, "satellites": 8, "latitude": 10.0, "longitude": 76.0, "data_available": True, "data_fresh": True, "data_age_ms": 100}
        with patch("bench_soak.read_live", return_value=live), patch("bench_soak.read_nmea", return_value=(3, 3)):
            result = run("http://bridge", "bridge", 10110, 3, 0, 1, 3000, 1)
        self.assertTrue(result["passed"])
        self.assertEqual(result["schema"], 3)
        self.assertEqual(result["passed_samples"], 3)
        self.assertEqual(result["failed_samples"], 0)
        self.assertEqual(result["min_nmea_sentences"], 1)
        self.assertLessEqual(result["started_at_unix_ms"], result["ended_at_unix_ms"])
        self.assertTrue(all("observed_at_unix_ms" in item for item in result["observations"]))
        self.assertTrue(all(item["nmea_valid_percent"] == 100.0 for item in result["observations"]))

    def test_single_failed_sample_fails_run_and_reports_checksum_rate(self):
        live = {"fix": True, "satellites": 8, "latitude": 10.0, "longitude": 76.0, "data_available": True, "data_fresh": True, "data_age_ms": 100}
        with patch("bench_soak.read_live", return_value=live), patch("bench_soak.read_nmea", side_effect=[(3, 3), (2, 1), (3, 3)]):
            result = run("http://bridge", "bridge", 10110, 3, 0, 1, 3000, 1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["passed_samples"], 2)
        self.assertEqual(result["failed_samples"], 1)
        self.assertFalse(result["observations"][1]["passed"])
        self.assertEqual(result["observations"][1]["nmea_valid_percent"], 50.0)

    def test_low_sentence_count_fails_sample(self):
        live = {"fix": True, "satellites": 8, "latitude": 10.0, "longitude": 76.0, "data_available": True, "data_fresh": True, "data_age_ms": 100}
        with patch("bench_soak.read_live", return_value=live), patch("bench_soak.read_nmea", return_value=(2, 2)):
            result = run("http://bridge", "bridge", 10110, 1, 0, 1, 3000, 3)
        self.assertFalse(result["passed"])
        self.assertEqual(result["failed_samples"], 1)
        self.assertIn("minimum is 3", result["observations"][0]["errors"])

    def test_transport_error_is_preserved_in_evidence(self):
        with patch("bench_soak.read_live", side_effect=OSError("offline")), patch("bench_soak.read_nmea", return_value=(0, 0)):
            result = run("http://bridge", "bridge", 10110, 1, 0, 1, 3000, 1)
        self.assertFalse(result["passed"])
        self.assertIn("HTTP diagnostics: offline", result["observations"][0]["errors"])


if __name__ == "__main__":
    unittest.main()

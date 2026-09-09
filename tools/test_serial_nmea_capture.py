import unittest
from collections import Counter

from serial_nmea_capture import build_report, checksum_ok, sentence_kind


class SerialNmeaCaptureTests(unittest.TestCase):
    def test_checksum_and_sentence_kind(self):
        sentence = "$GPRMC,1,2*44"
        self.assertTrue(checksum_ok(sentence))
        self.assertEqual(sentence_kind(sentence), "GPRMC")
        self.assertFalse(checksum_ok("$GPRMC,1,2*00"))
        self.assertIsNone(sentence_kind("not-nmea"))

    def test_quality_gate_passes(self):
        report = build_report(
            "COM5", 9600, 10.0, 10.01, 20, 20, 0,
            Counter({"GNRMC": 10, "GNGGA": 10}),
            10, 100.0, ["GNRMC", "GNGGA"],
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["schema"], 2)
        self.assertEqual(report["valid_percent"], 100.0)

    def test_quality_gate_rejects_sparse_capture(self):
        report = build_report(
            "COM5", 9600, 60.0, 60.0, 2, 2, 0,
            Counter({"GNRMC": 2}),
            10, 100.0, ["GNRMC"],
        )
        self.assertFalse(report["passed"])
        self.assertTrue(any("< 10" in failure for failure in report["failures"]))

    def test_quality_gate_rejects_bad_checksum_rate(self):
        report = build_report(
            "COM5", 9600, 10.0, 10.0, 10, 9, 1,
            Counter({"GNRMC": 9}),
            1, 100.0, ["GNRMC"],
        )
        self.assertFalse(report["passed"])
        self.assertTrue(any("valid NMEA percentage" in failure for failure in report["failures"]))

    def test_quality_gate_rejects_missing_required_type(self):
        report = build_report(
            "COM5", 9600, 10.0, 10.0, 10, 10, 0,
            Counter({"GNRMC": 10}),
            1, 100.0, ["GNRMC", "GNGGA"],
        )
        self.assertFalse(report["passed"])
        self.assertTrue(any("GNGGA" in failure for failure in report["failures"]))


if __name__ == "__main__":
    unittest.main()

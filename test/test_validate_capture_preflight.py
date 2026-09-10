import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.validate_capture_preflight import preflight


class ValidateCapturePreflightTests(unittest.TestCase):
    def test_all_checks_pass(self):
        run = Path("capture")
        capture = {"duration_s": 10.0, "live_samples": 10, "nmea_sentences": 5}
        integrity = {"valid": True}
        timing = {"valid": True}
        with patch("tools.validate_capture_preflight.validate_capture", return_value=capture), patch(
            "tools.validate_capture_preflight.validate_integrity", return_value=integrity
        ), patch("tools.validate_capture_preflight.validate_timing", return_value=timing):
            result = preflight(
                run,
                max_http_errors=0,
                max_nmea_reconnects=0,
                min_live_rate=0.5,
                min_nmea_sentences=1,
            )
        self.assertTrue(result["passed"])
        self.assertEqual([check["name"] for check in result["checks"]], ["capture", "integrity", "timing", "quality"])

    def test_quality_failure_fails_preflight(self):
        run = Path("capture")
        capture = {"duration_s": 10.0, "live_samples": 1, "nmea_sentences": 0, "http_errors": 1}
        with patch("tools.validate_capture_preflight.validate_capture", return_value=capture), patch(
            "tools.validate_capture_preflight.validate_integrity", return_value={"valid": True}
        ), patch("tools.validate_capture_preflight.validate_timing", return_value={"valid": True}):
            result = preflight(
                run,
                max_http_errors=0,
                max_nmea_reconnects=0,
                min_live_rate=0.5,
                min_nmea_sentences=1,
            )
        self.assertFalse(result["passed"])
        quality = next(check for check in result["checks"] if check["name"] == "quality")
        self.assertFalse(quality["passed"])
        self.assertTrue(quality["result"]["failures"])

    def test_check_exception_is_reported(self):
        run = Path("capture")
        with patch(
            "tools.validate_capture_preflight.validate_capture",
            side_effect=ValueError("missing CAPTURE.json"),
        ), patch("tools.validate_capture_preflight.validate_integrity", return_value={"valid": True}), patch(
            "tools.validate_capture_preflight.validate_timing", return_value={"valid": True}
        ):
            result = preflight(
                run,
                max_http_errors=0,
                max_nmea_reconnects=0,
                min_live_rate=0.5,
                min_nmea_sentences=1,
            )
        self.assertFalse(result["passed"])
        capture = next(check for check in result["checks"] if check["name"] == "capture")
        self.assertEqual(capture["error"], "missing CAPTURE.json")
        quality = next(check for check in result["checks"] if check["name"] == "quality")
        self.assertEqual(quality["error"], "missing CAPTURE.json")


if __name__ == "__main__":
    unittest.main()

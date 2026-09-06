import unittest

import capture_field_evidence


class CaptureFieldEvidenceTests(unittest.TestCase):
    def test_rejects_non_positive_duration(self):
        with self.assertRaises(SystemExit):
            capture_field_evidence.main(["http://127.0.0.1", "/tmp/out", "--duration", "0"])

    def test_rejects_invalid_port(self):
        with self.assertRaises(SystemExit):
            capture_field_evidence.main(["http://127.0.0.1", "/tmp/out", "--nmea-port", "70000"])

    def test_rejects_non_positive_timeout(self):
        with self.assertRaises(SystemExit):
            capture_field_evidence.main(["http://127.0.0.1", "/tmp/out", "--timeout", "0"])

    def test_rejects_non_positive_reconnect_interval(self):
        with self.assertRaises(SystemExit):
            capture_field_evidence.main(["http://127.0.0.1", "/tmp/out", "--reconnect-interval", "0"])

    def test_module_has_main(self):
        self.assertTrue(callable(capture_field_evidence.main))

    def test_timeline_format_is_documented_by_source(self):
        source = open(capture_field_evidence.__file__, encoding="utf-8").read()
        self.assertIn('timeline("CONNECT"', source)
        self.assertIn('timeline("DISCONNECT"', source)
        self.assertIn('timeline("NMEA", text)', source)
        self.assertIn('"nmea_timeline": "nmea_timeline.log"', source)


if __name__ == "__main__":
    unittest.main()

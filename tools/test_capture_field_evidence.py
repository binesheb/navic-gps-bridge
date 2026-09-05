import contextlib
import io
import unittest
from unittest.mock import patch

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

    def test_module_has_main(self):
        self.assertTrue(callable(capture_field_evidence.main))


if __name__ == "__main__":
    unittest.main()

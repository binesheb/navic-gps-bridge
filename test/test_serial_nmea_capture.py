import unittest

from tools.serial_nmea_capture import checksum_ok


class SerialNmeaCaptureTests(unittest.TestCase):
    def test_accepts_valid_checksum(self):
        self.assertTrue(checksum_ok("$GPRMC,123519,A,4807.038,N,01131.000,E,0.0,0.0,230394,,,A*70"))

    def test_rejects_invalid_checksum(self):
        self.assertFalse(checksum_ok("$GPRMC,123519,A,4807.038,N,01131.000,E,0.0,0.0,230394,,,A*00"))

    def test_rejects_missing_checksum(self):
        self.assertFalse(checksum_ok("$GPRMC,123519,A"))


if __name__ == "__main__":
    unittest.main()

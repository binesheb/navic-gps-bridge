import unittest

from tools.bench_smoke import checksum_ok, base_host


class BenchSmokeTests(unittest.TestCase):
    def test_accepts_valid_nmea_checksum(self):
        self.assertTrue(checksum_ok("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"))

    def test_rejects_invalid_nmea_checksum(self):
        self.assertFalse(checksum_ok("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*00"))

    def test_extracts_tcp_host_from_url(self):
        self.assertEqual(base_host("http://192.168.4.1:8080"), "192.168.4.1")


if __name__ == "__main__":
    unittest.main()

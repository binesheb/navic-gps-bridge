import unittest

from tools.bench_smoke import checksum_ok, base_host, validate_live


class BenchSmokeTests(unittest.TestCase):
    def test_accepts_valid_nmea_checksum(self):
        self.assertTrue(checksum_ok("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"))

    def test_rejects_invalid_nmea_checksum(self):
        self.assertFalse(checksum_ok("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*00"))

    def test_extracts_tcp_host_from_url(self):
        self.assertEqual(base_host("http://192.168.4.1:8080"), "192.168.4.1")

    def test_accepts_fresh_live_snapshot(self):
        validate_live({
            "fix": True,
            "satellites": 8,
            "latitude": 10.0,
            "longitude": 76.0,
            "data_available": True,
            "data_fresh": True,
            "data_age_ms": 250,
        }, 3000)

    def test_rejects_stale_live_snapshot(self):
        with self.assertRaisesRegex(RuntimeError, "stale GNSS data"):
            validate_live({
                "fix": False,
                "satellites": 0,
                "latitude": 0.0,
                "longitude": 0.0,
                "data_available": True,
                "data_fresh": False,
                "data_age_ms": 5000,
            }, 3000)

    def test_rejects_missing_live_diagnostics(self):
        with self.assertRaisesRegex(RuntimeError, "missing fields"):
            validate_live({"fix": False}, 3000)


if __name__ == "__main__":
    unittest.main()

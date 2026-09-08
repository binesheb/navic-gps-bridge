import unittest

from tools.bench_smoke import validate_live


VALID_LIVE = {
    "fix": True,
    "satellites": 8,
    "latitude": 10.0,
    "longitude": 76.0,
    "data_available": True,
    "data_fresh": True,
    "data_age_ms": 250,
}


class BenchSmokeSchemaTests(unittest.TestCase):
    def test_rejects_out_of_range_coordinates(self):
        with self.assertRaisesRegex(RuntimeError, "latitude"):
            validate_live(dict(VALID_LIVE, latitude=91.0), 3000)
        with self.assertRaisesRegex(RuntimeError, "longitude"):
            validate_live(dict(VALID_LIVE, longitude=-181.0), 3000)

    def test_rejects_non_finite_coordinates(self):
        with self.assertRaisesRegex(RuntimeError, "latitude"):
            validate_live(dict(VALID_LIVE, latitude=float("nan")), 3000)
        with self.assertRaisesRegex(RuntimeError, "longitude"):
            validate_live(dict(VALID_LIVE, longitude=float("inf")), 3000)

    def test_rejects_invalid_satellite_count(self):
        with self.assertRaisesRegex(RuntimeError, "satellites"):
            validate_live(dict(VALID_LIVE, satellites=-1), 3000)
        with self.assertRaisesRegex(RuntimeError, "satellites"):
            validate_live(dict(VALID_LIVE, satellites=2.5), 3000)

    def test_rejects_invalid_data_age(self):
        with self.assertRaisesRegex(RuntimeError, "data age"):
            validate_live(dict(VALID_LIVE, data_age_ms=float("nan")), 3000)
        with self.assertRaisesRegex(RuntimeError, "data age"):
            validate_live(dict(VALID_LIVE, data_age_ms=-1), 3000)

    def test_rejects_non_boolean_status_flags(self):
        with self.assertRaisesRegex(RuntimeError, "fix"):
            validate_live(dict(VALID_LIVE, fix=1), 3000)
        with self.assertRaisesRegex(RuntimeError, "no GNSS data"):
            validate_live(dict(VALID_LIVE, data_available=1), 3000)


if __name__ == "__main__":
    unittest.main()

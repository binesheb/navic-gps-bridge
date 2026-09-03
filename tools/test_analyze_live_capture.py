#!/usr/bin/env python3
import csv
import tempfile
import unittest
from pathlib import Path

from analyze_live_capture import analyze

FIELDS = ["http_ok", "data_fresh", "uptime_ms", "recovery_attempts", "data_available"]


class AnalyzeLiveCaptureTests(unittest.TestCase):
    def _write(self, rows, fields=FIELDS):
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8")
        with handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return handle.name

    def test_stable_capture_passes(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "2000", "recovery_attempts": "0", "data_available": "True"},
        ])
        self.assertEqual(analyze(path), [])

    def test_uptime_regression_fails(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "2000", "recovery_attempts": "0", "data_available": "True"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True"},
        ])
        self.assertTrue(any("uptime_ms" in failure for failure in analyze(path)))

    def test_recovery_limit_is_enforced(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "4", "data_available": "False"},
        ])
        self.assertTrue(any("recovery attempts" in failure for failure in analyze(path, max_recovery_attempts=3)))

    def test_missing_required_columns_fails(self):
        path = self._write(
            [{"http_ok": "True", "uptime_ms": "1000"}],
            fields=["http_ok", "uptime_ms"],
        )
        failures = analyze(path)
        self.assertTrue(any("missing required columns" in failure for failure in failures))

    def test_invalid_boolean_value_fails(self):
        path = self._write([
            {"http_ok": "maybe", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True"},
        ])
        self.assertTrue(any("invalid http_ok" in failure for failure in analyze(path)))

    def test_invalid_numeric_value_fails_without_crashing(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "not-a-number", "recovery_attempts": "0", "data_available": "True"},
        ])
        self.assertTrue(any("invalid uptime_ms" in failure for failure in analyze(path)))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import csv
import tempfile
import unittest
from pathlib import Path

from analyze_live_capture import analyze

FIELDS = ["http_ok", "data_fresh", "uptime_ms", "recovery_attempts", "data_available", "elapsed_s"]


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
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "0.0"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "2000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "1.0"},
        ])
        self.assertEqual(analyze(path), [])

    def test_failed_http_sample_does_not_create_false_telemetry_failure(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "0.0"},
            {"http_ok": "False", "data_fresh": "", "uptime_ms": "1001", "recovery_attempts": "0", "data_available": "", "elapsed_s": "1.0"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "2000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "2.0"},
        ])
        self.assertEqual(analyze(path, min_http_success=60.0), [])

    def test_http_failure_rate_is_enforced(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "0.0"},
            {"http_ok": "False", "data_fresh": "", "uptime_ms": "1001", "recovery_attempts": "0", "data_available": "", "elapsed_s": "1.0"},
        ])
        failures = analyze(path, min_http_success=75.0)
        self.assertTrue(any("HTTP success" in failure for failure in failures))

    def test_uptime_regression_fails(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "2000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "0.0"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "1.0"},
        ])
        self.assertTrue(any("uptime_ms" in failure for failure in analyze(path)))

    def test_elapsed_regression_fails(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "2.0"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "2000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "1.0"},
        ])
        self.assertTrue(any("elapsed_s moved backwards" in failure for failure in analyze(path)))

    def test_recovery_limit_uses_attempts_during_capture(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "4", "data_available": "False", "elapsed_s": "0.0"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "2000", "recovery_attempts": "5", "data_available": "True", "elapsed_s": "1.0"},
        ])
        failures = analyze(path, max_recovery_attempts=0)
        self.assertTrue(any("during capture" in failure for failure in failures))

    def test_preexisting_recovery_counter_does_not_satisfy_minimum(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "7", "data_available": "True", "elapsed_s": "0.0"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "2000", "recovery_attempts": "7", "data_available": "True", "elapsed_s": "1.0"},
        ])
        failures = analyze(path, min_recovery_attempts=1)
        self.assertTrue(any("during capture" in failure for failure in failures))

    def test_recovery_counter_delta_satisfies_minimum(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "7", "data_available": "False", "elapsed_s": "0.0"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "2000", "recovery_attempts": "8", "data_available": "True", "elapsed_s": "1.0"},
        ])
        self.assertEqual(analyze(path, min_recovery_attempts=1), [])

    def test_prolonged_stale_period_is_enforced(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "0.0"},
            {"http_ok": "True", "data_fresh": "False", "uptime_ms": "2000", "recovery_attempts": "1", "data_available": "False", "elapsed_s": "1.0"},
            {"http_ok": "True", "data_fresh": "False", "uptime_ms": "3000", "recovery_attempts": "1", "data_available": "False", "elapsed_s": "2.0"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "4000", "recovery_attempts": "1", "data_available": "True", "elapsed_s": "3.0"},
        ])
        failures = analyze(path, min_fresh=50.0, max_stale_samples=1)
        self.assertTrue(any("consecutive stale samples" in failure for failure in failures))

    def test_stale_period_resets_after_fresh_sample(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "False", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "False", "elapsed_s": "0.0"},
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "2000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "1.0"},
            {"http_ok": "True", "data_fresh": "False", "uptime_ms": "3000", "recovery_attempts": "0", "data_available": "False", "elapsed_s": "2.0"},
        ])
        self.assertEqual(analyze(path, min_fresh=30.0, max_stale_samples=1), [])

    def test_missing_required_columns_fails(self):
        path = self._write(
            [{"http_ok": "True", "uptime_ms": "1000"}],
            fields=["http_ok", "uptime_ms"],
        )
        failures = analyze(path)
        self.assertTrue(any("missing required columns" in failure for failure in failures))

    def test_invalid_boolean_value_fails(self):
        path = self._write([
            {"http_ok": "maybe", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "0.0"},
        ])
        self.assertTrue(any("invalid http_ok" in failure for failure in analyze(path)))

    def test_missing_boolean_value_fails(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "0.0"},
        ])
        self.assertTrue(any("missing data_fresh" in failure for failure in analyze(path)))

    def test_invalid_numeric_value_fails_without_crashing(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "not-a-number", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "0.0"},
        ])
        self.assertTrue(any("invalid uptime_ms" in failure for failure in analyze(path)))

    def test_missing_uptime_value_fails(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "", "recovery_attempts": "0", "data_available": "True", "elapsed_s": "0.0"},
        ])
        self.assertTrue(any("missing uptime_ms" in failure for failure in analyze(path)))

    def test_missing_elapsed_value_fails(self):
        path = self._write([
            {"http_ok": "True", "data_fresh": "True", "uptime_ms": "1000", "recovery_attempts": "0", "data_available": "True", "elapsed_s": ""},
        ])
        self.assertTrue(any("missing elapsed_s" in failure for failure in analyze(path)))


if __name__ == "__main__":
    unittest.main()

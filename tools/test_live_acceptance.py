#!/usr/bin/env python3
"""Self-tests for live acceptance command-line validation."""

import contextlib
import io
import unittest

import live_acceptance


class LiveAcceptanceValidationTests(unittest.TestCase):
    def assert_parser_error(self, *args: str) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                live_acceptance.main(["http://127.0.0.1", "capture.csv", *args])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("error:", stderr.getvalue())

    def test_rejects_non_finite_interval(self) -> None:
        self.assert_parser_error("--interval", "nan")

    def test_rejects_non_finite_duration(self) -> None:
        self.assert_parser_error("--duration", "inf")

    def test_rejects_non_finite_http_threshold(self) -> None:
        self.assert_parser_error("--min-http-success", "nan")

    def test_rejects_non_finite_fresh_threshold(self) -> None:
        self.assert_parser_error("--min-fresh", "-inf")

    def test_rejects_non_finite_minimum_duration(self) -> None:
        self.assert_parser_error("--min-duration-s", "nan")


if __name__ == "__main__":
    unittest.main()

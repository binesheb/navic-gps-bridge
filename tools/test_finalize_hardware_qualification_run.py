#!/usr/bin/env python3
"""Regression tests for hardware qualification finalization parsing."""

import unittest

from finalize_hardware_qualification_run import MATRIX_IDS, parse_matrix_results


class MatrixParsingTests(unittest.TestCase):
    def test_parses_standard_markdown_rows(self):
        text = "\n".join(
            f"| {case_id} | Scenario | Evidence | PASS |"
            for case_id in MATRIX_IDS
        )
        results = parse_matrix_results(text)
        self.assertEqual(results, {case_id: "PASS" for case_id in MATRIX_IDS})

    def test_preserves_non_pass_results(self):
        text = "\n".join(
            f"| {case_id} | Scenario | Evidence | {'FAIL' if case_id == 'H07' else 'NOT_RUN'} |"
            for case_id in MATRIX_IDS
        )
        results = parse_matrix_results(text)
        self.assertEqual(results["H07"], "FAIL")
        self.assertEqual(results["H01"], "NOT_RUN")

    def test_ignores_unrelated_rows(self):
        results = parse_matrix_results("| note | Scenario | Evidence | PASS |\n")
        self.assertEqual(results, {})


if __name__ == "__main__":
    unittest.main()

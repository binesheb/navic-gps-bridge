#!/usr/bin/env python3
"""Regression tests for physical qualification finalization gates."""

import unittest

from finalize_hardware_qualification_run import (
    MATRIX_IDS,
    parse_matrix_results,
    validate_field_acceptance_identity,
)


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


class FieldAcceptanceIdentityTests(unittest.TestCase):
    METADATA = {
        "test_id": "receiver-a-2026-09-09",
        "device": "bridge-01",
        "firmware_commit": "abc123",
        "receiver": "receiver-a",
    }

    def acceptance(self, **overrides):
        identity = {
            "test_id": self.METADATA["test_id"],
            "device_id": self.METADATA["device"],
            "firmware_revision": self.METADATA["firmware_commit"],
            "receiver_model": self.METADATA["receiver"],
        }
        identity.update(overrides)
        return {"schema_version": 3, "identity": identity, "passed": True}

    def test_accepts_matching_identity(self):
        validate_field_acceptance_identity(self.METADATA, self.acceptance())

    def test_rejects_missing_identity(self):
        with self.assertRaises(SystemExit) as context:
            validate_field_acceptance_identity(self.METADATA, {"schema_version": 3})
        self.assertIn("must contain identity metadata", str(context.exception))

    def test_rejects_mismatched_firmware(self):
        with self.assertRaises(SystemExit) as context:
            validate_field_acceptance_identity(
                self.METADATA,
                self.acceptance(firmware_revision="different-commit"),
            )
        self.assertIn("firmware_revision", str(context.exception))
        self.assertIn("does not match", str(context.exception))

    def test_rejects_mismatched_device(self):
        with self.assertRaises(SystemExit) as context:
            validate_field_acceptance_identity(
                self.METADATA,
                self.acceptance(device_id="bridge-02"),
            )
        self.assertIn("device_id", str(context.exception))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for physical qualification finalization gates."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from finalize_hardware_qualification_run import (
    MANIFEST_REQUIRED_FILES,
    MATRIX_IDS,
    parse_matrix_results,
    validate_capture_integrity,
    validate_evidence_manifest,
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


class CaptureIntegrityFinalizationTests(unittest.TestCase):
    def test_accepts_independently_verified_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            (run_dir / "CAPTURE.json").write_text("{}\n", encoding="utf-8")
            with patch(
                "finalize_hardware_qualification_run.verify_capture_integrity",
                return_value={"status": "PASS", "checked_files": 3, "mismatches": []},
            ) as verifier:
                validate_capture_integrity(run_dir)
            verifier.assert_called_once_with(run_dir)

    def test_rejects_tampered_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            (run_dir / "CAPTURE.json").write_text("{}\n", encoding="utf-8")
            with patch(
                "finalize_hardware_qualification_run.verify_capture_integrity",
                return_value={
                    "status": "FAIL",
                    "checked_files": 3,
                    "mismatches": [{"name": "live.csv", "reason": "hash_or_size_mismatch"}],
                },
            ):
                with self.assertRaises(SystemExit) as context:
                    validate_capture_integrity(run_dir)
            self.assertIn("capture integrity verification failed", str(context.exception))
            self.assertIn("live.csv", str(context.exception))

    def test_rejects_verifier_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            (run_dir / "CAPTURE.json").write_text("{}\n", encoding="utf-8")
            with patch(
                "finalize_hardware_qualification_run.verify_capture_integrity",
                side_effect=ValueError("missing required evidence"),
            ):
                with self.assertRaises(SystemExit) as context:
                    validate_capture_integrity(run_dir)
            self.assertIn("CAPTURE.json integrity verification failed", str(context.exception))
            self.assertIn("missing required evidence", str(context.exception))


class EvidenceManifestCoverageTests(unittest.TestCase):
    def _write_manifest(self, run_dir: Path, names):
        import hashlib
        import json

        entries = []
        for name in names:
            path = run_dir / name
            path.write_text(name + "\n", encoding="utf-8")
            entries.append(
                {
                    "name": name,
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        (run_dir / "EVIDENCE_MANIFEST.json").write_text(
            json.dumps({"schema": 1, "files": entries}, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_accepts_complete_manifest_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            self._write_manifest(run_dir, MANIFEST_REQUIRED_FILES)
            validate_evidence_manifest(run_dir)

    def test_rejects_manifest_missing_required_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            self._write_manifest(run_dir, MANIFEST_REQUIRED_FILES[:-1])
            with self.assertRaises(SystemExit) as context:
                validate_evidence_manifest(run_dir)
            self.assertIn("does not cover required evidence files", str(context.exception))
            self.assertIn(MANIFEST_REQUIRED_FILES[-1], str(context.exception))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for hardware qualification run preflight."""

import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_hardware_qualification_run import MATRIX_IDS, REQUIRED_FILES, validate_run


class HardwareRunPreflightTests(unittest.TestCase):
    def make_run(self) -> Path:
        root = Path(tempfile.mkdtemp())
        metadata = {
            "schema_version": 1,
            "status": "NOT_STARTED",
            "test_id": "receiver-a-2026-09-07",
            "device": "bridge-01",
            "board": "ESP32-S3",
            "firmware_commit": "abc123",
            "receiver": "receiver-a",
            "receiver_firmware": "1.0",
            "antenna": "external",
            "uart_baud": 9600,
            "operator": "operator",
            "started_at": "2026-09-07T14:00:00Z",
            "completed_at": None,
        }
        (root / "RUN_METADATA.json").write_text(json.dumps(metadata), encoding="utf-8")
        rows = "\n".join(f"| {case_id} | Scenario | NOT_RUN | |" for case_id in MATRIX_IDS)
        (root / "FIELD_QUALIFICATION_RUN.md").write_text(
            "# Hardware Qualification Run\n\n| ID | Scenario | Result | Evidence / notes |\n|---|---|---|---|\n" + rows + "\n",
            encoding="utf-8",
        )
        for name in REQUIRED_FILES[2:]:
            (root / name).write_text("{}\n" if name.endswith(".json") else "placeholder\n", encoding="utf-8")
        return root

    def test_accepts_complete_scaffold(self):
        self.assertEqual(validate_run(self.make_run()), [])

    def test_rejects_missing_matrix_row(self):
        root = self.make_run()
        path = root / "FIELD_QUALIFICATION_RUN.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace("| H14 | Scenario | NOT_RUN | |", "")
        path.write_text(text, encoding="utf-8")
        self.assertIn("missing checklist row: H14", validate_run(root))

    def test_rejects_finalized_run(self):
        root = self.make_run()
        path = root / "RUN_METADATA.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata["status"] = "COMPLETE"
        path.write_text(json.dumps(metadata), encoding="utf-8")
        self.assertIn("run is already COMPLETE", validate_run(root))


if __name__ == "__main__":
    unittest.main()

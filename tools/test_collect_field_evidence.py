#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "collect_field_evidence.py"


class FieldEvidenceTests(unittest.TestCase):
    def run_tool(self, *args):
        return subprocess.run(
            [sys.executable, str(TOOL), *map(str, args)],
            text=True,
            capture_output=True,
        )

    def test_copies_files_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "nmea.json"
            source.write_text('{"passed": true}\n', encoding="utf-8")
            output = root / "evidence"

            result = self.run_tool(
                output,
                "--file", f"nmea-verdict.json={source}",
                "--firmware-commit", "abc123",
                "--device", "bridge-01",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((output / "nmea-verdict.json").read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))
            manifest = json.loads((output / "EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], 1)
            self.assertEqual(manifest["firmware_commit"], "abc123")
            self.assertEqual(manifest["files"][0]["name"], "nmea-verdict.json")
            self.assertEqual(len(manifest["files"][0]["sha256"]), 64)

    def test_rejects_missing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_tool(
                Path(temp) / "evidence",
                "--file", f"missing.log={Path(temp) / 'missing.log'}",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not exist", result.stderr)

    def test_rejects_path_traversal_name(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "serial.log"
            source.write_text("ok\n", encoding="utf-8")
            result = self.run_tool(
                Path(temp) / "evidence",
                "--file", f"../serial.log={source}",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("simple filename", result.stderr)


if __name__ == "__main__":
    unittest.main()

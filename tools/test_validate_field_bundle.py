#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "validate_field_bundle.py"


class FieldBundleValidatorTests(unittest.TestCase):
    def run_tool(self, manifest: Path):
        return subprocess.run([sys.executable, str(TOOL), str(manifest)], text=True, capture_output=True)

    def make_bundle(self, root: Path, complete=True):
        evidence = root / "evidence"
        evidence.mkdir()
        files = {
            "nmea-verdict.json": "{\"passed\":true}\n",
            "live.csv": "elapsed_ms,state\n0,HEALTHY\n",
            "serial.log": "boot\n",
        }
        for name, content in files.items():
            (evidence / name).write_text(content, encoding="utf-8")
        entries = [{"name": name, "bytes": (evidence / name).stat().st_size, "sha256": "0" * 64} for name in files]
        if not complete:
            entries.pop()
        manifest = evidence / "EVIDENCE_MANIFEST.json"
        manifest.write_text(json.dumps({
            "schema": 1,
            "firmware_commit": "abc123",
            "device": "bridge-01",
            "receiver": "receiver-01",
            "test_id": "field-001",
            "files": entries,
        }) + "\n", encoding="utf-8")
        return manifest

    def test_accepts_complete_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_tool(self.make_bundle(Path(temp)))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["passed"])

    def test_rejects_missing_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = self.make_bundle(Path(temp))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["receiver"] = ""
            manifest.write_text(json.dumps(data), encoding="utf-8")
            result = self.run_tool(manifest)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("receiver", result.stdout)

    def test_rejects_missing_required_file(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_tool(self.make_bundle(Path(temp), complete=False))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required evidence files", result.stdout)


if __name__ == "__main__":
    unittest.main()

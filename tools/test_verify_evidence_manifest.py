#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "verify_evidence_manifest.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EvidenceManifestVerifierTests(unittest.TestCase):
    def run_tool(self, manifest):
        return subprocess.run(
            [sys.executable, str(TOOL), str(manifest)],
            text=True,
            capture_output=True,
        )

    def make_bundle(self, root: Path):
        evidence = root / "evidence"
        evidence.mkdir()
        nmea = evidence / "nmea.log"
        live = evidence / "live.csv"
        nmea.write_text("$GNGGA,1*00\n", encoding="utf-8")
        live.write_text("elapsed_ms,state\n0,HEALTHY\n", encoding="utf-8")
        manifest = evidence / "EVIDENCE_MANIFEST.json"
        manifest.write_text(json.dumps({
            "schema": 1,
            "created_utc": "2026-09-06T00:00:00+00:00",
            "files": [
                {"name": nmea.name, "bytes": nmea.stat().st_size, "sha256": digest(nmea)},
                {"name": live.name, "bytes": live.stat().st_size, "sha256": digest(live)},
            ],
        }) + "\n", encoding="utf-8")
        return evidence, manifest, nmea

    def test_accepts_matching_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            _, manifest, _ = self.make_bundle(Path(temp))
            result = self.run_tool(manifest)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["passed"])
            self.assertEqual(report["files_verified"], 2)

    def test_detects_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            _, manifest, nmea = self.make_bundle(Path(temp))
            nmea.write_text("tampered\n", encoding="utf-8")
            result = self.run_tool(manifest)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SHA-256 mismatch", result.stdout)

    def test_rejects_manifest_self_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence, manifest, _ = self.make_bundle(Path(temp))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["files"].append({"name": "EVIDENCE_MANIFEST.json", "bytes": manifest.stat().st_size, "sha256": digest(manifest)})
            manifest.write_text(json.dumps(data), encoding="utf-8")
            result = self.run_tool(manifest)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not list itself", result.stdout)

    def test_rejects_malformed_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            _, manifest, _ = self.make_bundle(Path(temp))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["files"][0]["sha256"] = "ABC"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            result = self.run_tool(manifest)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid SHA-256 digest", result.stdout)


if __name__ == "__main__":
    unittest.main()

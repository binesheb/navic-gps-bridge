#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import field_qualification_report as report


def qualification():
    return {
        "schema_version": 1,
        "qualification_ready": True,
        "passed": True,
        "health_sequence": "HEALTHY -> STALE -> RECOVERING -> HEALTHY",
        "recovery": {"duration_s": 4.5},
        "nmea_outage": {"duration_s": 3.2, "disconnect_count": 1, "connect_count": 1},
        "evidence_sha256": {
            "CAPTURE.json": "a" * 64,
            "live.csv": "b" * 64,
            "nmea_timeline.log": "c" * 64,
        },
    }


class FieldQualificationReportTests(unittest.TestCase):
    def test_manifest_metadata_is_rendered(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "EVIDENCE_MANIFEST.json"
            path.write_text(json.dumps({
                "schema": 1,
                "device": "bridge-01",
                "firmware_commit": "abc123",
                "receiver": "u-blox M10",
                "test_id": "recovery-01",
            }), encoding="utf-8")
            metadata = report._manifest_metadata(report._load_object(path, "evidence manifest"))
            text = report.render(qualification(), metadata=metadata)
            self.assertIn("**Device:** `bridge-01`", text)
            self.assertIn("**Firmware commit:** `abc123`", text)
            self.assertIn("**GNSS receiver:** `u-blox M10`", text)
            self.assertIn("**Test ID:** `recovery-01`", text)

    def test_cli_metadata_must_match_manifest(self):
        with self.assertRaises(ValueError):
            report._merge_metadata(
                {"device": "bridge-01"},
                {"device": "bridge-02"},
            )

    def test_manifest_rejects_wrong_schema(self):
        with self.assertRaises(ValueError):
            report._manifest_metadata({"schema": 2})


if __name__ == "__main__":
    unittest.main()

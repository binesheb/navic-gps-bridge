import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from field_acceptance import main


class FieldAcceptanceIdentityTests(unittest.TestCase):
    def test_identity_metadata_is_required_and_written(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            with patch("field_acceptance._run", side_effect=[(0, ""), (0, "")]):
                rc = main([
                    "http://192.168.4.1",
                    str(output),
                    "--device-id", "bridge-01",
                    "--firmware-revision", "abc123",
                    "--receiver-model", "u-blox-M10",
                    "--test-id", "H01-001",
                ])
            self.assertEqual(rc, 0)
            report = json.loads((output / "FIELD_ACCEPTANCE.json").read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], 3)
            self.assertEqual(report["identity"], {
                "device_id": "bridge-01",
                "firmware_revision": "abc123",
                "receiver_model": "u-blox-M10",
                "test_id": "H01-001",
            })

    def test_identity_metadata_is_rejected_when_partial(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(SystemExit):
                main(["http://192.168.4.1", temp, "--device-id", "bridge-01"])


if __name__ == "__main__":
    unittest.main()

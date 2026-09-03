import hashlib
import tempfile
import unittest
from pathlib import Path

import verify_build_artifact


class VerifyBuildArtifactTests(unittest.TestCase):
    def make_bundle(self, firmware=b"navic-test-firmware"):
        root = Path(tempfile.mkdtemp())
        firmware_path = root / "firmware.bin"
        firmware_path.write_bytes(firmware)
        digest = hashlib.sha256(firmware).hexdigest()
        (root / "SHA256SUMS").write_text(f"{digest}  firmware.bin\n", encoding="utf-8")
        (root / "BUILD_INFO.txt").write_text(
            "repository=binesheb/navic-gps-bridge\n"
            "commit=abc123\n"
            "build_target=esp32-s3-devkitc-1\n"
            f"firmware_sha256={digest}\n"
            f"firmware_bytes={len(firmware)}\n",
            encoding="utf-8",
        )
        return root

    def test_manifest_parser(self):
        bundle = self.make_bundle()
        values = verify_build_artifact.parse_manifest(bundle / "BUILD_INFO.txt")
        self.assertEqual(values["build_target"], "esp32-s3-devkitc-1")

    def test_checksum(self):
        bundle = self.make_bundle()
        expected = hashlib.sha256((bundle / "firmware.bin").read_bytes()).hexdigest()
        self.assertEqual(verify_build_artifact.sha256(bundle / "firmware.bin"), expected)

    def test_manifest_parser_rejects_malformed_line(self):
        path = Path(tempfile.mkdtemp()) / "bad.txt"
        path.write_text("not-a-key-value-line\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_build_artifact.parse_manifest(path)


if __name__ == "__main__":
    unittest.main()

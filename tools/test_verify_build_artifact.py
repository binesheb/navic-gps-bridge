import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import verify_build_artifact


class VerifyBuildArtifactTests(unittest.TestCase):
    def make_bundle(self, firmware=b"navic-test-firmware"):
        root = Path(tempfile.mkdtemp())
        artifacts = {
            "firmware.bin": firmware,
            "bootloader.bin": b"navic-test-bootloader",
            "partitions.bin": b"navic-test-partitions",
        }
        hashes = {}
        for name, data in artifacts.items():
            (root / name).write_bytes(data)
            hashes[name] = hashlib.sha256(data).hexdigest()

        (root / "SHA256SUMS").write_text(
            "".join(f"{digest}  {name}\n" for name, digest in hashes.items()),
            encoding="utf-8",
        )
        (root / "BUILD_INFO.txt").write_text(
            "repository=binesheb/navic-gps-bridge\n"
            "commit=abc123\n"
            "build_target=esp32-s3-devkitc-1\n"
            f"firmware_sha256={hashes['firmware.bin']}\n"
            f"firmware_bytes={len(artifacts['firmware.bin'])}\n"
            f"bootloader_sha256={hashes['bootloader.bin']}\n"
            f"bootloader_bytes={len(artifacts['bootloader.bin'])}\n"
            f"partitions_sha256={hashes['partitions.bin']}\n"
            f"partitions_bytes={len(artifacts['partitions.bin'])}\n",
            encoding="utf-8",
        )
        return root

    def run_verifier(self, bundle):
        with mock.patch("sys.argv", [
            "verify_build_artifact.py", str(bundle),
            "--repository", "binesheb/navic-gps-bridge",
            "--commit", "abc123",
        ]):
            return verify_build_artifact.main()

    def test_manifest_parser(self):
        bundle = self.make_bundle()
        values = verify_build_artifact.parse_manifest(bundle / "BUILD_INFO.txt")
        self.assertEqual(values["build_target"], "esp32-s3-devkitc-1")

    def test_checksum(self):
        bundle = self.make_bundle()
        expected = hashlib.sha256((bundle / "firmware.bin").read_bytes()).hexdigest()
        self.assertEqual(verify_build_artifact.sha256(bundle / "firmware.bin"), expected)

    def test_bundle_verifies_all_components(self):
        bundle = self.make_bundle()
        self.assertEqual(self.run_verifier(bundle), 0)

    def test_checksum_manifest_rejects_missing_component(self):
        bundle = self.make_bundle()
        (bundle / "bootloader.bin").unlink()
        with self.assertRaises(SystemExit):
            self.run_verifier(bundle)

    def test_checksum_parser_rejects_duplicate(self):
        path = Path(tempfile.mkdtemp()) / "sums.txt"
        digest = hashlib.sha256(b"x").hexdigest()
        path.write_text(f"{digest}  firmware.bin\n{digest}  firmware.bin\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_build_artifact.parse_sums(path)

    def test_manifest_parser_rejects_duplicate_key(self):
        path = Path(tempfile.mkdtemp()) / "bad.txt"
        path.write_text("commit=one\ncommit=two\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_build_artifact.parse_manifest(path)

    def test_manifest_parser_rejects_malformed_line(self):
        path = Path(tempfile.mkdtemp()) / "bad.txt"
        path.write_text("not-a-key-value-line\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_build_artifact.parse_manifest(path)


if __name__ == "__main__":
    unittest.main()

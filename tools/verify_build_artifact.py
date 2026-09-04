#!/usr/bin/env python3
"""Verify the integrity and provenance of a NavIC GPS Bridge firmware bundle."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ARTIFACTS = ("firmware.bin", "bootloader.bin", "partitions.bin")


def parse_manifest(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition("=")
        if not sep or not key:
            raise ValueError(f"invalid manifest line: {line!r}")
        if key in values:
            raise ValueError(f"duplicate manifest key: {key!r}")
        values[key] = value
    return values


def parse_sums(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 2:
            raise ValueError(f"invalid checksum line: {line!r}")
        digest, name = fields
        if len(digest) != 64 or any(char not in "0123456789abcdefABCDEF" for char in digest):
            raise ValueError(f"invalid SHA-256 digest for {name!r}")
        if name in values:
            raise ValueError(f"duplicate checksum entry: {name!r}")
        values[name] = digest.lower()
    return values


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="production firmware build directory")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()

    bundle = args.bundle
    sums = bundle / "SHA256SUMS"
    manifest = bundle / "BUILD_INFO.txt"

    for path in (sums, manifest):
        if not path.is_file():
            raise SystemExit(f"missing build artifact: {path}")

    checksums = parse_sums(sums)
    values = parse_manifest(manifest)

    for name in ARTIFACTS:
        path = bundle / name
        if not path.is_file():
            raise SystemExit(f"missing build artifact: {path}")
        actual = sha256(path)
        expected = checksums.get(name)
        if expected != actual:
            raise SystemExit(
                f"checksum mismatch for {name}: expected {expected!r}, got {actual!r}"
            )

        manifest_key = name.removesuffix(".bin") + "_sha256"
        manifest_size_key = name.removesuffix(".bin") + "_bytes"
        if values.get(manifest_key) != actual:
            raise SystemExit(
                f"manifest mismatch for {manifest_key}: "
                f"expected {actual!r}, got {values.get(manifest_key)!r}"
            )
        if values.get(manifest_size_key) != str(path.stat().st_size):
            raise SystemExit(
                f"manifest mismatch for {manifest_size_key}: "
                f"expected {path.stat().st_size!r}, got {values.get(manifest_size_key)!r}"
            )

    required = {
        "repository": args.repository,
        "commit": args.commit,
        "build_target": "esp32-s3-devkitc-1",
    }
    for key, expected_value in required.items():
        actual_value = values.get(key)
        if actual_value != expected_value:
            raise SystemExit(
                f"manifest mismatch for {key}: expected {expected_value!r}, got {actual_value!r}"
            )

    print(f"Verified firmware bundle: {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

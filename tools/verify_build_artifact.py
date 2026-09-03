#!/usr/bin/env python3
"""Verify the integrity and provenance of a NavIC GPS Bridge firmware bundle."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def parse_manifest(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition("=")
        if not sep or not key:
            raise ValueError(f"invalid manifest line: {line!r}")
        values[key] = value
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
    firmware = bundle / "firmware.bin"
    sums = bundle / "SHA256SUMS"
    manifest = bundle / "BUILD_INFO.txt"

    for path in (firmware, sums, manifest):
        if not path.is_file():
            raise SystemExit(f"missing build artifact: {path}")

    expected = sums.read_text(encoding="utf-8").split()[0]
    actual = sha256(firmware)
    if expected != actual:
        raise SystemExit(f"firmware checksum mismatch: expected {expected}, got {actual}")

    values = parse_manifest(manifest)
    required = {
        "repository": args.repository,
        "commit": args.commit,
        "build_target": "esp32-s3-devkitc-1",
        "firmware_sha256": actual,
        "firmware_bytes": str(firmware.stat().st_size),
    }
    for key, expected_value in required.items():
        actual_value = values.get(key)
        if actual_value != expected_value:
            raise SystemExit(
                f"manifest mismatch for {key}: expected {expected_value!r}, got {actual_value!r}"
            )

    print(f"Verified firmware bundle: {firmware} ({actual})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

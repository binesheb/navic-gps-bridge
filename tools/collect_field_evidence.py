#!/usr/bin/env python3
"""Collect reproducible GNSS field-test evidence with the canonical manifest."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

try:
    from tools.generate_evidence_manifest import build_manifest
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from generate_evidence_manifest import build_manifest


def parse_file_spec(value: str) -> tuple[str, Path]:
    name, separator, raw_path = value.partition("=")
    if not separator or not name or not raw_path:
        raise argparse.ArgumentTypeError("expected NAME=PATH")
    if Path(name).name != name or name in {"", ".", ".."}:
        raise argparse.ArgumentTypeError("NAME must be a simple filename")
    return name, Path(raw_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="directory for the evidence bundle")
    parser.add_argument("--file", dest="files", action="append", type=parse_file_spec,
                        metavar="NAME=PATH", required=True,
                        help="evidence file to copy; may be repeated")
    parser.add_argument("--firmware-commit", required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--receiver", required=True,
                        help="GNSS receiver model/identifier used for the test")
    parser.add_argument("--test-id", required=True,
                        help="unique operator-assigned field test identifier")
    args = parser.parse_args(argv)

    identity = {
        "firmware_commit": args.firmware_commit.strip(),
        "device": args.device.strip(),
        "receiver": args.receiver.strip(),
        "test_id": args.test_id.strip(),
    }
    if any(not value for value in identity.values()):
        parser.error("identity metadata must be non-empty")

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    names = []
    for name, source_arg in args.files:
        if name in names:
            parser.error(f"duplicate evidence name: {name}")
        source = source_arg.resolve()
        if not source.is_file():
            parser.error(f"evidence file does not exist: {source}")
        shutil.copy2(source, output / name)
        names.append(name)

    try:
        manifest = build_manifest(output, names, **identity)
    except ValueError as exc:
        parser.error(str(exc))

    manifest_path = output / "EVIDENCE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

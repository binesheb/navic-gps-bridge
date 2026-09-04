#!/usr/bin/env python3
"""Collect reproducible GNSS field-test evidence with a SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_file_spec(value: str) -> tuple[str, Path]:
    name, separator, raw_path = value.partition("=")
    if not separator or not name or not raw_path:
        raise argparse.ArgumentTypeError("expected NAME=PATH")
    if Path(name).name != name or name in {"", ".", ".."}:
        raise argparse.ArgumentTypeError("NAME must be a simple filename")
    return name, Path(raw_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="directory for the evidence bundle")
    parser.add_argument("--file", dest="files", action="append", type=parse_file_spec,
                        metavar="NAME=PATH", required=True,
                        help="evidence file to copy; may be repeated")
    parser.add_argument("--firmware-commit", default=None)
    parser.add_argument("--device", default=None)
    parser.add_argument("--notes", default=None)
    args = parser.parse_args()

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    entries = []
    seen_names = set()
    for name, source_arg in args.files:
        source = source_arg.resolve()
        if name in seen_names:
            parser.error(f"duplicate evidence name: {name}")
        seen_names.add(name)
        if not source.is_file():
            parser.error(f"evidence file does not exist: {source}")
        destination = output / name
        if destination.resolve().parent != output:
            parser.error(f"invalid destination: {name}")
        shutil.copy2(source, destination)
        entries.append({
            "name": name,
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
        })

    manifest = {
        "schema": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "firmware_commit": args.firmware_commit,
        "device": args.device,
        "notes": args.notes,
        "files": entries,
    }
    manifest_path = output / "EVIDENCE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

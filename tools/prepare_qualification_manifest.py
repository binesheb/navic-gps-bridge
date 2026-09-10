#!/usr/bin/env python3
"""Generate a qualification evidence manifest directly from RUN_METADATA.json.

The helper closes the operator-error gap between a qualification run scaffold
and its final evidence manifest. It reads the run identity from
RUN_METADATA.json, requires every stable physical evidence artifact to be
present and non-empty, and delegates hashing/schema construction to the
canonical manifest builder. Derived qualification records are validated by the
finalizer separately because they are produced after evidence collection.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.create_hardware_qualification_run import MANIFEST_EVIDENCE_FILES
from tools.generate_evidence_manifest import build_manifest

REQUIRED_IDENTITY = ("device", "firmware_commit", "receiver", "test_id")


def load_metadata(run: Path) -> dict:
    path = run / "RUN_METADATA.json"
    if not path.is_file():
        raise ValueError("RUN_METADATA.json is missing")
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid RUN_METADATA.json: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError("RUN_METADATA.json must contain an object")
    return metadata


def prepare_manifest(run: Path) -> dict:
    run = run.resolve()
    metadata = load_metadata(run)
    missing_identity = [key for key in REQUIRED_IDENTITY if not str(metadata.get(key, "")).strip()]
    if missing_identity:
        raise ValueError("missing identity metadata: " + ", ".join(missing_identity))

    evidence_names = list(MANIFEST_EVIDENCE_FILES)
    missing = []
    empty = []
    for name in evidence_names:
        path = run / name
        if not path.is_file():
            missing.append(name)
        elif path.stat().st_size == 0:
            empty.append(name)
    if missing:
        raise ValueError("missing evidence files: " + ", ".join(missing))
    if empty:
        raise ValueError("empty evidence files: " + ", ".join(empty))

    return build_manifest(
        run,
        evidence_names,
        device=str(metadata["device"]),
        firmware_commit=str(metadata["firmware_commit"]),
        receiver=str(metadata["receiver"]),
        test_id=str(metadata["test_id"]),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="qualification run directory")
    args = parser.parse_args(argv)

    try:
        manifest = prepare_manifest(args.run)
    except ValueError as exc:
        parser.error(str(exc))

    output = args.run.resolve() / "EVIDENCE_MANIFEST.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

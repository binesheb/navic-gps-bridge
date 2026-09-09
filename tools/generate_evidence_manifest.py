#!/usr/bin/env python3
"""Create a deterministic SHA-256 manifest for a field-evidence directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Field-evidence directory")
    parser.add_argument("--output", type=Path, default=None, help="Manifest path (default: RUN/EVIDENCE_MANIFEST.json)")
    parser.add_argument("--files", nargs="+", required=True, help="Evidence filenames to include")
    parser.add_argument("--device", required=True)
    parser.add_argument("--firmware-commit", required=True)
    parser.add_argument("--receiver", required=True)
    parser.add_argument("--test-id", required=True)
    return parser.parse_args()


def build_manifest(run: Path, names: list[str], *, device: str, firmware_commit: str, receiver: str, test_id: str) -> dict:
    run = run.resolve()
    if not run.is_dir():
        raise ValueError(f"evidence directory does not exist: {run}")

    normalized = []
    for name in names:
        path = Path(name)
        if path.name != name or name in {"", ".", ".."}:
            raise ValueError(f"evidence filenames must be simple filenames: {name!r}")
        if name == "EVIDENCE_MANIFEST.json":
            raise ValueError("manifest must not include itself")
        if name not in normalized:
            normalized.append(name)

    files = []
    for name in sorted(normalized):
        path = run / name
        if not path.is_file():
            raise ValueError(f"evidence file does not exist: {name}")
        files.append({"name": name, "bytes": path.stat().st_size, "sha256": sha256(path)})

    return {
        "schema": 1,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "device": device.strip(),
        "firmware_commit": firmware_commit.strip(),
        "receiver": receiver.strip(),
        "test_id": test_id.strip(),
        "files": files,
    }


def main() -> int:
    args = parse_args()
    try:
        values = {key: value for key, value in {"device": args.device, "firmware_commit": args.firmware_commit, "receiver": args.receiver, "test_id": args.test_id}.items()}
        if any(not value.strip() for value in values.values()):
            raise ValueError("identity metadata must be non-empty")
        manifest = build_manifest(args.run, args.files, **values)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    output = (args.output or (args.run / "EVIDENCE_MANIFEST.json")).resolve()
    if output.parent != args.run.resolve():
        raise SystemExit("manifest output must be inside the evidence directory")
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

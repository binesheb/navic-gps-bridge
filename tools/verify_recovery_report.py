#!/usr/bin/env python3
"""Verify that a recovery qualification report still matches its evidence bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(report_path: Path, bundle: Path) -> dict:
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid qualification report: {exc}") from exc
    if not isinstance(report, dict):
        raise ValueError("qualification report must contain an object")
    expected = report.get("evidence_sha256")
    if not isinstance(expected, dict):
        raise ValueError("qualification report is missing evidence_sha256")
    required = {"CAPTURE.json", "live.csv", "nmea_timeline.log"}
    if set(expected) != required:
        raise ValueError("evidence_sha256 must contain exactly CAPTURE.json, live.csv, and nmea_timeline.log")

    results = {}
    for name in sorted(required):
        path = bundle / name
        if not path.is_file():
            raise ValueError(f"bundle is missing {name}")
        actual = sha256_file(path)
        results[name] = {"expected": expected[name], "actual": actual, "match": actual == expected[name]}

    passed = all(item["match"] for item in results.values())
    return {"passed": passed, "report": str(report_path), "bundle": str(bundle), "evidence": results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    parser.add_argument("bundle_dir")
    parser.add_argument("--json-output")
    args = parser.parse_args(argv)
    try:
        result = verify(Path(args.report), Path(args.bundle_dir))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        Path(args.json_output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

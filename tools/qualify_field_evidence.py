#!/usr/bin/env python3
"""Qualify a NavIC GPS Bridge field-evidence bundle deterministically."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from verify_field_evidence import verify_bundle

MANIFEST_NAME = "EVIDENCE_MANIFEST.json"


def load_json(path: pathlib.Path) -> dict:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read JSON {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def qualify(bundle: str, expected_commit: str | None = None,
            nmea_name: str = "nmea-verdict.json",
            live_name: str = "live-verdict.json") -> tuple[dict, list[str]]:
    root = pathlib.Path(bundle).resolve()
    failures: list[str] = []
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        failures.append(f"FAIL: missing {MANIFEST_NAME}")
        return {"schema_version": 1, "passed": False, "bundle": str(root), "failures": failures}, failures

    try:
        manifest = load_json(manifest_path)
    except ValueError as exc:
        failures.append(f"FAIL: {exc}")
        return {"schema_version": 1, "passed": False, "bundle": str(root), "failures": failures}, failures

    if manifest.get("schema") != 1:
        failures.append("FAIL: unsupported manifest schema")

    # Qualification must include integrity verification, not merely trust the manifest.
    failures.extend(f"FAIL: {failure}" for failure in verify_bundle(root))

    firmware_commit = manifest.get("firmware_commit")
    if not isinstance(firmware_commit, str) or not firmware_commit.strip():
        failures.append("FAIL: manifest is missing firmware_commit")
    if expected_commit is not None and firmware_commit != expected_commit:
        failures.append(f"FAIL: firmware commit {firmware_commit!r} != expected {expected_commit!r}")

    entries = manifest.get("files")
    if not isinstance(entries, list):
        failures.append("FAIL: manifest files must be a list")
        entries = []
    filenames = {
        entry["name"] for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    for required in (nmea_name, live_name):
        if required not in filenames:
            failures.append(f"FAIL: manifest does not include required verdict {required}")

    verdicts: dict[str, dict] = {}
    for name in (nmea_name, live_name):
        path = root / name
        if not path.is_file():
            failures.append(f"FAIL: missing required verdict file {name}")
            continue
        try:
            verdicts[name] = load_json(path)
        except ValueError as exc:
            failures.append(f"FAIL: {exc}")

    for name, verdict in verdicts.items():
        if verdict.get("passed") is not True:
            failures.append(f"FAIL: {name} does not report passed=true")

    report = {
        "schema_version": 1,
        "bundle": str(root),
        "firmware_commit": firmware_commit,
        "required_verdicts": [nmea_name, live_name],
        "integrity_verified": not any("integrity" in failure.lower() for failure in failures),
        "nmea_passed": verdicts.get(nmea_name, {}).get("passed") is True,
        "live_passed": verdicts.get(live_name, {}).get("passed") is True,
        "passed": not failures,
        "failures": failures,
    }
    return report, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Field evidence bundle directory")
    parser.add_argument("--firmware-commit", help="Require this exact firmware commit")
    parser.add_argument("--nmea-verdict", default="nmea-verdict.json")
    parser.add_argument("--live-verdict", default="live-verdict.json")
    parser.add_argument("--json-output", help="Write the qualification report to this path")
    args = parser.parse_args(argv)

    if args.nmea_verdict == args.live_verdict:
        parser.error("nmea-verdict and live-verdict must name different files")
    report, failures = qualify(
        args.bundle, args.firmware_commit, args.nmea_verdict, args.live_verdict
    )
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

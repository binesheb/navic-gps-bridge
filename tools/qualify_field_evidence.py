#!/usr/bin/env python3
"""Qualify a NavIC GPS Bridge field-evidence bundle deterministically."""

from __future__ import annotations

import argparse
import json
import pathlib

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
            live_name: str = "live-verdict.json",
            health_sequence_name: str | None = None) -> tuple[dict, list[str]]:
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

    integrity_failures = verify_bundle(root)
    failures.extend(f"FAIL: {failure}" for failure in integrity_failures)

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
    if health_sequence_name is not None and health_sequence_name not in filenames:
        failures.append(
            f"FAIL: manifest does not include required health-sequence verdict {health_sequence_name}"
        )

    required_verdict_names = [nmea_name, live_name]
    if health_sequence_name is not None:
        required_verdict_names.append(health_sequence_name)

    verdicts: dict[str, dict] = {}
    for name in required_verdict_names:
        path = root / name
        if not path.is_file():
            failures.append(f"FAIL: missing required verdict file {name}")
            continue
        try:
            verdicts[name] = load_json(path)
        except ValueError as exc:
            failures.append(f"FAIL: {exc}")

    for name in required_verdict_names:
        verdict = verdicts.get(name)
        if verdict is None:
            continue
        if verdict.get("passed") is not True:
            failures.append(f"FAIL: {name} does not report passed=true")

    health_sequence_passed = None
    if health_sequence_name is not None:
        health_sequence = verdicts.get(health_sequence_name, {})
        health_sequence_passed = health_sequence.get("qualification_ready") is True
        if not health_sequence_passed:
            failures.append(
                f"FAIL: {health_sequence_name} does not report qualification_ready=true"
            )

    report = {
        "schema_version": 1,
        "bundle": str(root),
        "firmware_commit": firmware_commit,
        "required_verdicts": required_verdict_names,
        "integrity_verified": not integrity_failures,
        "nmea_passed": verdicts.get(nmea_name, {}).get("passed") is True,
        "live_passed": verdicts.get(live_name, {}).get("passed") is True,
        "health_sequence_passed": health_sequence_passed,
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
    parser.add_argument("--health-sequence-verdict", help="Require a passing physical recovery-sequence verdict")
    parser.add_argument("--json-output", help="Write the qualification report to this path")
    args = parser.parse_args(argv)

    if args.nmea_verdict == args.live_verdict:
        parser.error("nmea-verdict and live-verdict must name different files")
    if args.health_sequence_verdict in {args.nmea_verdict, args.live_verdict}:
        parser.error("health-sequence-verdict must name a distinct file")
    report, failures = qualify(
        args.bundle,
        args.firmware_commit,
        args.nmea_verdict,
        args.live_verdict,
        args.health_sequence_verdict,
    )
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run the complete offline field-evidence qualification pipeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from field_qualification_report import render
from qualify_recovery_bundle import validate_bundle
from validate_field_bundle import validate_manifest
from verify_evidence_manifest import verify as verify_manifest
from verify_recovery_report import verify as verify_recovery


def run(bundle: Path, output: Path, max_recovery_seconds=None, max_nmea_outage_seconds=None) -> dict:
    bundle = bundle.resolve()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = bundle / "EVIDENCE_MANIFEST.json"
    preflight = validate_manifest(manifest_path)
    if not preflight["passed"]:
        raise ValueError("field bundle preflight failed: " + preflight["error"])

    manifest_result = verify_manifest(manifest_path)
    if not manifest_result["passed"]:
        raise ValueError("evidence manifest verification failed: " + manifest_result["error"])

    qualification = validate_bundle(bundle, max_recovery_seconds, max_nmea_outage_seconds)
    qualification_path = output / "recovery-qualification.json"
    qualification_path.write_text(json.dumps(qualification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not qualification["qualification_ready"]:
        raise ValueError("recovery qualification did not pass")

    recovery_verification = verify_recovery(qualification_path, bundle)
    verification_path = output / "recovery-verification.json"
    verification_path.write_text(json.dumps(recovery_verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not recovery_verification["passed"]:
        raise ValueError("recovery evidence verification failed")

    report_path = output / "FIELD_QUALIFICATION.md"
    metadata = {key: preflight[key] for key in ("device", "firmware_commit", "receiver", "test_id")}
    report_path.write_text(render(qualification, recovery_verification, metadata), encoding="utf-8")

    result = {
        "passed": True,
        "preflight": preflight,
        "manifest_verification": manifest_result,
        "qualification": qualification,
        "recovery_verification": recovery_verification,
        "artifacts": [str(qualification_path), str(verification_path), str(report_path)],
    }
    (output / "FIELD_QUALIFICATION_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--max-recovery-seconds", type=float)
    parser.add_argument("--max-nmea-outage-seconds", type=float)
    args = parser.parse_args(argv)
    if not args.bundle_dir.is_dir():
        parser.error(f"bundle directory does not exist: {args.bundle_dir}")
    if args.max_recovery_seconds is not None and args.max_recovery_seconds < 0:
        parser.error("max-recovery-seconds must be >= 0")
    if args.max_nmea_outage_seconds is not None and args.max_nmea_outage_seconds < 0:
        parser.error("max-nmea-outage-seconds must be >= 0")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = run(args.bundle_dir, args.output_dir, args.max_recovery_seconds, args.max_nmea_outage_seconds)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

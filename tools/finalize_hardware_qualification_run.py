#!/usr/bin/env python3
"""Finalize a physical hardware qualification run without inventing results.

The operator checklist is the source of truth for H01-H14. This tool only
changes a run from IN_PROGRESS to COMPLETE when every matrix row is explicitly
marked PASS, the field-acceptance identity matches RUN_METADATA.json, all
required evidence files are present and non-empty, and the evidence manifest
verifies every stable physical evidence hash. Derived qualification records
are re-verified from the archived evidence before completion. It also records
the completion timestamp in RUN_METADATA.json.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    from tools.create_hardware_qualification_run import MANIFEST_EVIDENCE_FILES
    from tools.verify_evidence_manifest import verify as verify_evidence_manifest
    from tools.verify_recovery_report import verify as verify_recovery_report
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from create_hardware_qualification_run import MANIFEST_EVIDENCE_FILES
    from verify_evidence_manifest import verify as verify_evidence_manifest
    from verify_recovery_report import verify as verify_recovery_report

MATRIX_IDS = tuple(f"H{i:02d}" for i in range(1, 15))
REQUIRED_FILES = (
    "nmea-verdict.json",
    "live.csv",
    "serial.log",
    "EVIDENCE_MANIFEST.json",
    "recovery-qualification.json",
    "recovery-verification.json",
    "FIELD_ACCEPTANCE.json",
    "FIELD_QUALIFICATION.md",
    "FIELD_QUALIFICATION_RESULT.json",
)
MANIFEST_REQUIRED_FILES = MANIFEST_EVIDENCE_FILES
ROW_RE = re.compile(r"^\|\s*(H\d{2})\s*\|.*?\|\s*(PASS|FAIL|NOT_RUN)\s*\|", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Existing hardware qualification run directory")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{path.name} must contain a JSON object")
    return value


def parse_utc_timestamp(value: object, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"cannot finalize; RUN_METADATA.json has no valid {field_name} timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(f"cannot finalize; RUN_METADATA.json has invalid {field_name} timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SystemExit(f"cannot finalize; {field_name} timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def validate_run_state(metadata: dict) -> None:
    """Require an internally consistent physical-test lifecycle before finalization."""
    status = metadata.get("status")
    if status != "IN_PROGRESS":
        raise SystemExit(f"cannot finalize; run status must be IN_PROGRESS, got {status!r}")

    created_at = parse_utc_timestamp(metadata.get("created_at"), "creation")
    started_at = parse_utc_timestamp(metadata.get("started_at"), "physical test start")

    if started_at < created_at:
        raise SystemExit("cannot finalize; physical test start timestamp precedes run creation timestamp")
    if metadata.get("completed_at") is not None:
        raise SystemExit("cannot finalize; IN_PROGRESS run already contains a completion timestamp")


def parse_matrix_results(text: str) -> dict[str, str]:
    """Return the latest recognized result for each H01-H14 matrix row."""
    return {case_id: result for case_id, result in ROW_RE.findall(text)}


def validate_field_acceptance_identity(metadata: dict, acceptance: dict) -> None:
    identity = acceptance.get("identity")
    if not isinstance(identity, dict):
        raise SystemExit("FIELD_ACCEPTANCE.json must contain identity metadata before finalization")
    expected = {
        "device_id": metadata.get("device"),
        "firmware_revision": metadata.get("firmware_commit"),
        "receiver_model": metadata.get("receiver"),
        "test_id": metadata.get("test_id"),
    }
    missing = [key for key, value in expected.items() if not value]
    if missing:
        raise SystemExit("RUN_METADATA.json missing identity fields: " + ", ".join(missing))
    mismatched = [key for key, value in expected.items() if identity.get(key) != value]
    if mismatched:
        details = ", ".join(
            f"{key} expected={expected[key]!r} actual={identity.get(key)!r}" for key in mismatched
        )
        raise SystemExit("FIELD_ACCEPTANCE identity does not match RUN_METADATA.json: " + details)


def validate_evidence_manifest(run_dir: Path) -> None:
    result = verify_evidence_manifest(run_dir / "EVIDENCE_MANIFEST.json")
    if result.get("passed") is not True:
        raise SystemExit("EVIDENCE_MANIFEST.json verification failed: " + str(result.get("error", "unknown error")))
    verified_names = {entry.get("name") for entry in result.get("files", []) if isinstance(entry, dict)}
    missing = [name for name in MANIFEST_REQUIRED_FILES if name not in verified_names]
    if missing:
        raise SystemExit(
            "EVIDENCE_MANIFEST.json does not cover required evidence files (stable physical evidence): "
            + ", ".join(missing)
        )


def validate_recovery_evidence(run_dir: Path) -> None:
    """Recompute recovery evidence hashes instead of trusting a stored verdict."""
    stored = load_json(run_dir / "recovery-verification.json")
    if stored.get("passed") is not True:
        raise SystemExit("recovery-verification.json must contain passed=true")
    try:
        current = verify_recovery_report(run_dir / "recovery-qualification.json", run_dir)
    except (OSError, ValueError) as exc:
        raise SystemExit("recovery qualification evidence verification failed: " + str(exc)) from exc
    if current.get("passed") is not True:
        raise SystemExit("recovery qualification evidence no longer matches its recorded hashes")
    if stored.get("evidence") != current.get("evidence"):
        raise SystemExit("recovery-verification.json is stale; regenerate it from the archived evidence")


def main() -> int:
    args = parse_args()
    run_dir = args.run.resolve()
    metadata_path = run_dir / "RUN_METADATA.json"
    checklist_path = run_dir / "FIELD_QUALIFICATION_RUN.md"

    if not run_dir.is_dir():
        raise SystemExit(f"run directory does not exist: {run_dir}")
    metadata = load_json(metadata_path)
    if not checklist_path.is_file():
        raise SystemExit("missing FIELD_QUALIFICATION_RUN.md")
    validate_run_state(metadata)

    rows = parse_matrix_results(checklist_path.read_text(encoding="utf-8"))
    missing_rows = [case_id for case_id in MATRIX_IDS if case_id not in rows]
    if missing_rows:
        raise SystemExit("missing matrix rows: " + ", ".join(missing_rows))
    non_pass = [case_id for case_id in MATRIX_IDS if rows[case_id] != "PASS"]
    if non_pass:
        raise SystemExit("cannot finalize; matrix cases are not PASS: " + ", ".join(non_pass))

    missing = [name for name in REQUIRED_FILES if not (run_dir / name).is_file()]
    if missing:
        raise SystemExit("missing required evidence files: " + ", ".join(missing))
    empty = [name for name in REQUIRED_FILES if (run_dir / name).stat().st_size == 0]
    if empty:
        raise SystemExit("required evidence files are empty: " + ", ".join(empty))

    validate_evidence_manifest(run_dir)
    validate_field_acceptance_identity(metadata, load_json(run_dir / "FIELD_ACCEPTANCE.json"))
    validate_recovery_evidence(run_dir)

    result_path = run_dir / "FIELD_QUALIFICATION_RESULT.json"
    result = load_json(result_path)
    if result.get("passed") is not True:
        raise SystemExit("FIELD_QUALIFICATION_RESULT.json must contain passed=true")

    metadata["status"] = "COMPLETE"
    metadata["completed_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(f"hardware qualification run finalized: {run_dir}")
    print("matrix: H01-H14 PASS")
    print("evidence: present, non-empty, and stable physical manifest verified")
    print("field acceptance identity: matches RUN_METADATA.json")
    print("recovery evidence: independently re-verified and stored verdict matches")
    print("qualification result: passed=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

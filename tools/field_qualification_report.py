#!/usr/bin/env python3
"""Generate a human-readable field qualification report from machine verdicts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain an object")
    return value


def _fmt_seconds(value) -> str:
    if isinstance(value, (int, float)) and value >= 0:
        return f"{value:.3f} s"
    return "n/a"


def _metadata_items(metadata: dict | None) -> list[tuple[str, str]]:
    if metadata is None:
        return []
    if not isinstance(metadata, dict):
        raise ValueError("metadata must contain an object")
    allowed = {
        "device": "Device",
        "firmware_commit": "Firmware commit",
        "receiver": "GNSS receiver",
        "test_id": "Test ID",
    }
    items = []
    for key, label in allowed.items():
        value = metadata.get(key)
        if value is not None:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"metadata[{key}] must be a non-empty string")
            items.append((label, value.strip()))
    return items


def render(qualification: dict, verification: dict | None = None, metadata: dict | None = None) -> str:
    if qualification.get("schema_version") != 1:
        raise ValueError("qualification report schema_version must be 1")
    if qualification.get("qualification_ready") is not True:
        raise ValueError("qualification report is not qualification-ready")

    passed = qualification.get("passed") is True
    recovery = qualification.get("recovery", {})
    outage = qualification.get("nmea_outage", {})
    evidence = qualification.get("evidence_sha256", {})
    lines = [
        "# NavIC GPS Bridge — Field Qualification Report",
        "",
        f"**Result:** {'PASS' if passed else 'FAIL'}",
        f"**Qualification ready:** yes",
    ]

    metadata_items = _metadata_items(metadata)
    if metadata_items:
        lines.extend(["", "## Test identity", ""])
        lines.extend(f"- **{label}:** `{value}`" for label, value in metadata_items)

    lines.extend([
        "",
        "## Recovery",
        "",
        f"- Health sequence: `{qualification.get('health_sequence', 'n/a')}`",
        f"- Recovery duration: {_fmt_seconds(recovery.get('duration_s'))}",
        f"- NMEA outage duration: {_fmt_seconds(outage.get('duration_s'))}",
        f"- NMEA disconnects: {outage.get('disconnect_count', 'n/a')}",
        f"- NMEA reconnects: {outage.get('connect_count', 'n/a')}",
        "",
        "## Evidence integrity",
        "",
    ])
    for name in ("CAPTURE.json", "live.csv", "nmea_timeline.log"):
        digest = evidence.get(name, "n/a")
        lines.append(f"- `{name}`: `{digest}`")

    if verification is not None:
        if not isinstance(verification, dict):
            raise ValueError("verification result must contain an object")
        lines.extend([
            "",
            "## Post-test verification",
            "",
            f"- Evidence hashes match: {'yes' if verification.get('passed') is True else 'no'}",
        ])

    lines.extend([
        "",
        "## Operator notes",
        "",
        "- Preserve this report with the exact firmware commit and original evidence files.",
        "- A PASS is valid only for the captured hardware/receiver combination and test conditions.",
        "",
    ])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualification_report")
    parser.add_argument("output")
    parser.add_argument("--verification-report")
    parser.add_argument("--device")
    parser.add_argument("--firmware-commit")
    parser.add_argument("--receiver")
    parser.add_argument("--test-id")
    args = parser.parse_args(argv)

    qualification = _load_object(Path(args.qualification_report), "qualification report")
    verification = None
    if args.verification_report:
        verification = _load_object(Path(args.verification_report), "verification report")
    metadata = {
        key: value
        for key, value in {
            "device": args.device,
            "firmware_commit": args.firmware_commit,
            "receiver": args.receiver,
            "test_id": args.test_id,
        }.items()
        if value is not None
    }
    try:
        text = render(qualification, verification, metadata)
    except ValueError as exc:
        parser.error(str(exc))
    Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
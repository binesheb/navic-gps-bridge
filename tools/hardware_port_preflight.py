#!/usr/bin/env python3
"""Preflight a physical GNSS/ESP32 serial port before evidence capture.

This tool deliberately performs no writes to the target serial device. It verifies
that pyserial is available, the requested port exists, and the port can be opened
with the requested baud rate. When the OS exposes USB metadata, that identity is
recorded so a field run can prove which physical adapter was selected. Optional
identity expectations can fail closed before capture starts.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_usb_id(value: str) -> int:
    try:
        parsed = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("USB IDs must be hexadecimal (for example 0x10c4)") from exc
    if not 0 <= parsed <= 0xFFFF:
        raise argparse.ArgumentTypeError("USB IDs must be between 0x0000 and 0xffff")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that a physical serial port is ready for GNSS capture."
    )
    parser.add_argument("port", help="Serial port, e.g. COM5 or /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=9600, help="Expected baud rate")
    parser.add_argument("--expect-vid", type=parse_usb_id, help="Expected USB vendor ID, e.g. 0x10c4")
    parser.add_argument("--expect-pid", type=parse_usb_id, help="Expected USB product ID, e.g. 0xea60")
    parser.add_argument("--expect-serial-number", help="Expected USB serial number")
    parser.add_argument("--expect-manufacturer", help="Expected USB manufacturer string")
    parser.add_argument("--expect-product", help="Expected USB product string")
    parser.add_argument("--json-output", type=Path, help="Write a machine-readable verdict")
    return parser.parse_args()


def verdict(ok: bool, **fields: object) -> dict[str, object]:
    return {
        "passed": ok,
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        **fields,
    }


def port_identity(info: object) -> dict[str, object]:
    """Return stable, JSON-safe identity metadata exposed by pyserial."""
    fields = ("device", "vid", "pid", "serial_number", "manufacturer", "product", "location", "interface")
    return {field: getattr(info, field, None) for field in fields}


def identity_failures(
    identity: dict[str, object],
    expect_vid: int | None,
    expect_pid: int | None,
    expect_serial_number: str | None = None,
    expect_manufacturer: str | None = None,
    expect_product: str | None = None,
) -> list[str]:
    failures: list[str] = []
    checks = (
        ("vid", "USB vendor ID", expect_vid, lambda value: f"0x{value:04x}" if isinstance(value, int) else repr(value)),
        ("pid", "USB product ID", expect_pid, lambda value: f"0x{value:04x}" if isinstance(value, int) else repr(value)),
        ("serial_number", "USB serial number", expect_serial_number, repr),
        ("manufacturer", "USB manufacturer", expect_manufacturer, repr),
        ("product", "USB product", expect_product, repr),
    )
    for field, label, expected, formatter in checks:
        if expected is None:
            continue
        actual = identity.get(field)
        if actual != expected:
            failures.append(f"FAIL: {label} {formatter(actual)} != expected {formatter(expected)}")
    return failures


def main() -> int:
    args = parse_args()
    result: dict[str, object]

    if args.baud < 1200 or args.baud > 921600:
        result = verdict(
            False,
            port=args.port,
            baud=args.baud,
            error="invalid_baud",
            detail="baud must be between 1200 and 921600",
        )
    else:
        try:
            import serial
            from serial.tools import list_ports
        except ImportError:
            result = verdict(
                False,
                port=args.port,
                baud=args.baud,
                error="pyserial_missing",
                detail="install requirements-field.txt before physical capture",
            )
        else:
            port_info = next((item for item in list_ports.comports() if item.device == args.port), None)
            if port_info is None:
                result = verdict(
                    False,
                    port=args.port,
                    baud=args.baud,
                    error="port_not_found",
                    available_ports=sorted(item.device for item in list_ports.comports()),
                )
            else:
                identity = port_identity(port_info)
                failures = identity_failures(
                    identity,
                    args.expect_vid,
                    args.expect_pid,
                    args.expect_serial_number,
                    args.expect_manufacturer,
                    args.expect_product,
                )
                if failures:
                    result = verdict(
                        False,
                        port=args.port,
                        baud=args.baud,
                        error="port_identity_mismatch",
                        identity=identity,
                        failures=failures,
                    )
                else:
                    try:
                        with serial.Serial(args.port, args.baud, timeout=0) as connection:
                            opened = connection.is_open
                    except (OSError, serial.SerialException) as exc:
                        result = verdict(
                            False,
                            port=args.port,
                            baud=args.baud,
                            error="port_open_failed",
                            identity=identity,
                            detail=str(exc),
                        )
                    else:
                        result = verdict(
                            opened,
                            port=args.port,
                            baud=args.baud,
                            identity=identity,
                            error=None if opened else "port_not_open",
                            detail="port opened successfully; no bytes were transmitted",
                        )

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2))
    for failure in result.get("failures", []):
        print(failure)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

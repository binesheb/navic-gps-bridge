#!/usr/bin/env python3
"""Preflight a physical GNSS/ESP32 serial port before evidence capture.

This tool deliberately performs no writes to the target serial device. It verifies
that pyserial is available, the requested port exists, and the port can be opened
with the requested baud rate. It can optionally emit a JSON result for traceable
field logs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that a physical serial port is ready for GNSS capture."
    )
    parser.add_argument("port", help="Serial port, e.g. COM5 or /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=9600, help="Expected baud rate")
    parser.add_argument("--json-output", type=Path, help="Write a machine-readable verdict")
    return parser.parse_args()


def verdict(ok: bool, **fields: object) -> dict[str, object]:
    return {
        "passed": ok,
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        **fields,
    }


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
            ports = {item.device for item in list_ports.comports()}
            if args.port not in ports:
                result = verdict(
                    False,
                    port=args.port,
                    baud=args.baud,
                    error="port_not_found",
                    available_ports=sorted(ports),
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
                        detail=str(exc),
                    )
                else:
                    result = verdict(
                        opened,
                        port=args.port,
                        baud=args.baud,
                        error=None if opened else "port_not_open",
                        detail="port opened successfully; no bytes were transmitted",
                    )

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

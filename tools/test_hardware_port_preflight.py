#!/usr/bin/env python3
"""Regression tests for hardware_port_preflight.py."""

from __future__ import annotations

import unittest

import hardware_port_preflight


class HardwarePortPreflightTests(unittest.TestCase):
    def test_parse_usb_id_accepts_hex_and_decimal(self) -> None:
        self.assertEqual(hardware_port_preflight.parse_usb_id("0x10c4"), 0x10C4)
        self.assertEqual(hardware_port_preflight.parse_usb_id("60000"), 60000)

    def test_port_identity_is_json_safe_and_stable(self) -> None:
        class Info:
            device = "/dev/ttyUSB0"
            vid = 0x10C4
            pid = 0xEA60
            serial_number = "ABC123"
            manufacturer = "Silicon Labs"
            product = "CP210x"
            location = "1-2"
            interface = "0"

        self.assertEqual(
            hardware_port_preflight.port_identity(Info()),
            {
                "device": "/dev/ttyUSB0",
                "vid": 0x10C4,
                "pid": 0xEA60,
                "serial_number": "ABC123",
                "manufacturer": "Silicon Labs",
                "product": "CP210x",
                "location": "1-2",
                "interface": "0",
            },
        )

    def test_all_identity_expectations_match(self) -> None:
        identity = {
            "vid": 0x10C4,
            "pid": 0xEA60,
            "serial_number": "ABC123",
            "manufacturer": "Silicon Labs",
            "product": "CP210x",
            "location": "1-2",
            "interface": "0",
        }
        self.assertEqual(
            hardware_port_preflight.identity_failures(
                identity,
                0x10C4,
                0xEA60,
                "ABC123",
                "Silicon Labs",
                "CP210x",
                "1-2",
                "0",
            ),
            [],
        )

    def test_identity_mismatch_fails_closed(self) -> None:
        identity = {"vid": 0x10C4, "pid": 0xEA60, "location": "1-3", "interface": None}
        failures = hardware_port_preflight.identity_failures(
            identity,
            0x10C4,
            0xEA60,
            expect_location="1-2",
            expect_interface="0",
        )
        self.assertEqual(
            failures,
            [
                "FAIL: USB topology location '1-3' != expected '1-2'",
                "FAIL: USB interface None != expected '0'",
            ],
        )

    def test_missing_metadata_fails_when_expected(self) -> None:
        failures = hardware_port_preflight.identity_failures(
            {"vid": None, "pid": None, "location": None, "interface": None},
            0x10C4,
            0xEA60,
            expect_location="1-2",
            expect_interface="0",
        )
        self.assertEqual(
            failures,
            [
                "FAIL: USB vendor ID None != expected 0x10c4",
                "FAIL: USB product ID None != expected 0xea60",
                "FAIL: USB topology location None != expected '1-2'",
                "FAIL: USB interface None != expected '0'",
            ],
        )

    def test_unexpected_metadata_is_ignored_when_not_requested(self) -> None:
        identity = {"vid": 0x10C4, "pid": 0xEA60, "location": "different", "interface": "9"}
        self.assertEqual(
            hardware_port_preflight.identity_failures(identity, 0x10C4, 0xEA60),
            [],
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.hardware_port_preflight import identity_failures, port_identity


SCRIPT = Path(__file__).parents[1] / "tools" / "hardware_port_preflight.py"


def test_invalid_baud_fails_closed_and_writes_json(tmp_path: Path) -> None:
    output = tmp_path / "preflight.json"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "COM5", "--baud", "0", "--json-output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["passed"] is False
    assert result["error"] == "invalid_baud"
    assert result["port"] == "COM5"
    assert result["baud"] == 0


def test_port_identity_is_stable_and_json_safe() -> None:
    class Port:
        device = "COM5"
        vid = 0x10C4
        pid = 0xEA60
        serial_number = "ABC123"
        manufacturer = "Silicon Labs"
        product = "CP210x"
        location = "1-2"
        interface = "0"

    assert port_identity(Port()) == {
        "device": "COM5",
        "vid": 0x10C4,
        "pid": 0xEA60,
        "serial_number": "ABC123",
        "manufacturer": "Silicon Labs",
        "product": "CP210x",
        "location": "1-2",
        "interface": "0",
    }


def test_identity_expectations_fail_closed_on_mismatch() -> None:
    identity = {"vid": 0x10C4, "pid": 0xEA60}

    assert identity_failures(identity, 0x10C4, 0xEA60) == []
    failures = identity_failures(identity, 0x1A86, 0x7523)
    assert len(failures) == 2
    assert "vendor ID" in failures[0]
    assert "product ID" in failures[1]


def test_identity_expectation_fails_when_metadata_is_unavailable() -> None:
    failures = identity_failures({"vid": None, "pid": None}, 0x10C4, None)
    assert failures == ["FAIL: USB vendor ID None != expected 0x10c4"]

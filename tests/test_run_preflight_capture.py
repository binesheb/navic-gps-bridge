from __future__ import annotations

import json
from pathlib import Path

from tools import run_preflight_capture as runner


def test_failed_preflight_blocks_capture(tmp_path, monkeypatch):
    calls = []

    def fake_run(command, check=False):
        calls.append(command)
        return type("Result", (), {"returncode": 1})()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    assert runner.main(["/dev/ttyUSB0", "http://bridge", str(tmp_path)]) == 1
    assert len(calls) == 1
    assert "tools/capture_field_evidence.py" not in calls[0]


def test_passed_preflight_binds_identity_to_capture(tmp_path, monkeypatch):
    calls = []
    output = Path(tmp_path)

    def fake_run(command, check=False):
        calls.append(command)
        if "hardware_port_preflight.py" in command:
            (output / "HARDWARE_PREFLIGHT.json").write_text(
                json.dumps({
                    "passed": True,
                    "identity": {"device": "/dev/ttyUSB0", "vid": 0x10C4, "pid": 0xEA60},
                })
            )
        else:
            (output / "CAPTURE.json").write_text(json.dumps({"schema_version": 2}))
        return type("Result", (), {"returncode": 0})()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    assert runner.main(["/dev/ttyUSB0", "http://bridge", str(tmp_path)]) == 0

    report = json.loads((output / "CAPTURE.json").read_text())
    assert report["hardware_preflight"]["passed"] is True
    assert report["hardware_preflight"]["port"] == "/dev/ttyUSB0"
    assert report["hardware_preflight"]["identity"]["vid"] == 0x10C4
    assert len(calls) == 2
    assert "tools/capture_field_evidence.py" in calls[1]

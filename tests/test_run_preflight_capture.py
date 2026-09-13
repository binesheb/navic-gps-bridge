from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

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
    checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def fake_run(command, check=False):
        calls.append(command)
        if "hardware_port_preflight.py" in command:
            (output / "HARDWARE_PREFLIGHT.json").write_text(
                json.dumps({
                    "passed": True,
                    "checked_at": checked_at,
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
    assert report["hardware_preflight"]["checked_at"] == checked_at
    assert len(calls) == 2
    assert "tools/capture_field_evidence.py" in calls[1]


def test_stale_preflight_blocks_capture(tmp_path, monkeypatch):
    calls = []
    output = Path(tmp_path)
    stale = (datetime.now(timezone.utc) - timedelta(seconds=31)).isoformat().replace("+00:00", "Z")

    def fake_run(command, check=False):
        calls.append(command)
        if "hardware_port_preflight.py" in command:
            (output / "HARDWARE_PREFLIGHT.json").write_text(json.dumps({
                "passed": True,
                "checked_at": stale,
                "identity": {"device": "/dev/ttyUSB0"},
            }))
        else:
            raise AssertionError("capture must not run for stale preflight")
        return type("Result", (), {"returncode": 0})()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    assert runner.main(["/dev/ttyUSB0", "http://bridge", str(tmp_path)]) == 1
    assert len(calls) == 1


def test_missing_checked_at_blocks_capture(tmp_path, monkeypatch):
    output = Path(tmp_path)

    def fake_run(command, check=False):
        if "hardware_port_preflight.py" in command:
            (output / "HARDWARE_PREFLIGHT.json").write_text(json.dumps({
                "passed": True,
                "identity": {"device": "/dev/ttyUSB0"},
            }))
            return type("Result", (), {"returncode": 0})()
        raise AssertionError("capture must not run without checked_at")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    assert runner.main(["/dev/ttyUSB0", "http://bridge", str(tmp_path)]) == 1


def test_future_checked_at_blocks_capture():
    checked = datetime.now(timezone.utc) + timedelta(seconds=1)
    with pytest.raises(RuntimeError, match="in the future"):
        runner.validate_verdict_freshness(
            {"checked_at": checked.isoformat().replace("+00:00", "Z")},
            30,
            now=datetime.now(timezone.utc),
        )

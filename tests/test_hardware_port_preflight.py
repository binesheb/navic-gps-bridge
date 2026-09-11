from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


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

import json

import pytest

from tools.finalize_hardware_qualification_run import validate_run_state
from tools.start_hardware_qualification_run import main as start_main


def test_finalize_requires_in_progress_state():
    with pytest.raises(SystemExit, match="IN_PROGRESS"):
        validate_run_state({"status": "NOT_STARTED", "started_at": "2026-09-11T12:00:00Z"})


def test_finalize_requires_start_timestamp():
    with pytest.raises(SystemExit, match="start timestamp"):
        validate_run_state({"status": "IN_PROGRESS", "started_at": None})


def test_start_transitions_scaffold_to_in_progress(tmp_path, monkeypatch):
    run = tmp_path / "run"
    run.mkdir()
    metadata = {"status": "NOT_STARTED", "started_at": "2026-09-11T12:00:00Z", "completed_at": None}
    (run / "RUN_METADATA.json").write_text(json.dumps(metadata), encoding="utf-8")
    (run / "FIELD_QUALIFICATION_RUN.md").write_text("# Run\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["start_hardware_qualification_run.py", str(run)])

    assert start_main() == 0

    updated = json.loads((run / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert updated["status"] == "IN_PROGRESS"
    assert updated["completed_at"] is None
    assert updated["started_at"] != "2026-09-11T12:00:00Z"


def test_start_rejects_already_started_run(tmp_path, monkeypatch):
    run = tmp_path / "run"
    run.mkdir()
    (run / "RUN_METADATA.json").write_text(
        json.dumps({"status": "IN_PROGRESS", "started_at": "2026-09-11T12:00:00Z"}),
        encoding="utf-8",
    )
    (run / "FIELD_QUALIFICATION_RUN.md").write_text("# Run\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["start_hardware_qualification_run.py", str(run)])

    with pytest.raises(SystemExit, match="must be NOT_STARTED"):
        start_main()

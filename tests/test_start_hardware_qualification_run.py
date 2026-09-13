from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.start_hardware_qualification_run import start_run


def make_run(tmp_path: Path, status: str = "NOT_STARTED", started_at=None, completed_at=None) -> Path:
    run = tmp_path / "run"
    run.mkdir()
    (run / "RUN_METADATA.json").write_text(
        json.dumps({"schema_version": 1, "status": status, "started_at": started_at, "completed_at": completed_at}),
        encoding="utf-8",
    )
    (run / "FIELD_QUALIFICATION_RUN.md").write_text(
        "# Hardware Qualification Run\n\n- Overall result: `NOT_STARTED`\n\n| H01 | Scenario | NOT_RUN | |\n",
        encoding="utf-8",
    )
    return run


def test_start_run_transitions_lifecycle_without_touching_results(tmp_path: Path):
    run = make_run(tmp_path)
    started_at = start_run(run)

    metadata = json.loads((run / "RUN_METADATA.json").read_text(encoding="utf-8"))
    checklist = (run / "FIELD_QUALIFICATION_RUN.md").read_text(encoding="utf-8")

    assert metadata["status"] == "IN_PROGRESS"
    assert metadata["started_at"] == started_at
    assert metadata["completed_at"] is None
    assert "H01 | Scenario | NOT_RUN" in checklist
    assert "Overall result: `IN_PROGRESS`" in checklist
    assert "Overall result: `NOT_STARTED`" not in checklist


def test_start_run_rejects_non_not_started(tmp_path: Path):
    run = make_run(tmp_path, status="IN_PROGRESS", started_at="2026-09-13T00:00:00Z")
    with pytest.raises(SystemExit, match="status must be NOT_STARTED"):
        start_run(run)


def test_start_run_rejects_completed_run(tmp_path: Path):
    run = make_run(tmp_path, completed_at="2026-09-13T01:00:00Z")
    with pytest.raises(SystemExit, match="status must be NOT_STARTED"):
        start_run(run)

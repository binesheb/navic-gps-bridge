import json

import pytest

from tools.create_hardware_qualification_run import main as create_main
from tools.finalize_hardware_qualification_run import validate_run_state
from tools.start_hardware_qualification_run import main as start_main


def test_finalize_requires_in_progress_state():
    with pytest.raises(SystemExit, match="IN_PROGRESS"):
        validate_run_state({"status": "NOT_STARTED", "started_at": "2026-09-11T12:00:00Z"})


def test_finalize_requires_valid_creation_timestamp():
    with pytest.raises(SystemExit, match="creation"):
        validate_run_state({
            "status": "IN_PROGRESS",
            "created_at": "not-a-timestamp",
            "started_at": "2026-09-11T12:01:00Z",
            "completed_at": None,
        })


def test_finalize_requires_valid_start_timestamp():
    with pytest.raises(SystemExit, match="physical test start"):
        validate_run_state({
            "status": "IN_PROGRESS",
            "created_at": "2026-09-11T12:00:00Z",
            "started_at": "not-a-timestamp",
            "completed_at": None,
        })


def test_finalize_requires_start_after_creation():
    with pytest.raises(SystemExit, match="precedes run creation"):
        validate_run_state({
            "status": "IN_PROGRESS",
            "created_at": "2026-09-11T12:02:00Z",
            "started_at": "2026-09-11T12:01:00Z",
            "completed_at": None,
        })


def test_finalize_rejects_existing_completion_timestamp():
    with pytest.raises(SystemExit, match="completion timestamp"):
        validate_run_state({
            "status": "IN_PROGRESS",
            "created_at": "2026-09-11T12:00:00Z",
            "started_at": "2026-09-11T12:01:00Z",
            "completed_at": "2026-09-11T12:05:00Z",
        })


def test_finalize_accepts_consistent_lifecycle_timestamps():
    validate_run_state({
        "status": "IN_PROGRESS",
        "created_at": "2026-09-11T12:00:00Z",
        "started_at": "2026-09-11T12:01:00+00:00",
        "completed_at": None,
    })


def test_scaffold_records_creation_time_not_test_start(tmp_path, monkeypatch):
    run = tmp_path / "run"
    monkeypatch.setattr(
        "sys.argv",
        [
            "create_hardware_qualification_run.py",
            str(run),
            "--device",
            "device-01",
            "--receiver",
            "GNSS receiver",
            "--firmware-commit",
            "abcdef0",
            "--test-id",
            "HIL-001",
        ],
    )

    assert create_main() == 0

    metadata = json.loads((run / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "NOT_STARTED"
    assert metadata["created_at"]
    assert metadata["started_at"] is None


def test_start_transitions_scaffold_to_in_progress(tmp_path, monkeypatch):
    run = tmp_path / "run"
    run.mkdir()
    metadata = {
        "status": "NOT_STARTED",
        "created_at": "2026-09-11T12:00:00Z",
        "started_at": None,
        "completed_at": None,
    }
    (run / "RUN_METADATA.json").write_text(json.dumps(metadata), encoding="utf-8")
    (run / "FIELD_QUALIFICATION_RUN.md").write_text("# Run\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["start_hardware_qualification_run.py", str(run)])

    assert start_main() == 0

    updated = json.loads((run / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert updated["status"] == "IN_PROGRESS"
    assert updated["completed_at"] is None
    assert updated["started_at"] != "2026-09-11T12:00:00Z"
    assert updated["created_at"] == "2026-09-11T12:00:00Z"


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


def test_start_rejects_preexisting_start_timestamp(tmp_path, monkeypatch):
    run = tmp_path / "run"
    run.mkdir()
    (run / "RUN_METADATA.json").write_text(
        json.dumps(
            {
                "status": "NOT_STARTED",
                "created_at": "2026-09-11T12:00:00Z",
                "started_at": "2026-09-11T12:01:00Z",
                "completed_at": None,
            }
        ),
        encoding="utf-8",
    )
    (run / "FIELD_QUALIFICATION_RUN.md").write_text("# Run\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["start_hardware_qualification_run.py", str(run)])

    with pytest.raises(SystemExit, match="already contains a physical test start timestamp"):
        start_main()


def test_start_rejects_preexisting_completion_timestamp(tmp_path, monkeypatch):
    run = tmp_path / "run"
    run.mkdir()
    (run / "RUN_METADATA.json").write_text(
        json.dumps(
            {
                "status": "NOT_STARTED",
                "created_at": "2026-09-11T12:00:00Z",
                "started_at": None,
                "completed_at": "2026-09-11T12:05:00Z",
            }
        ),
        encoding="utf-8",
    )
    (run / "FIELD_QUALIFICATION_RUN.md").write_text("# Run\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["start_hardware_qualification_run.py", str(run)])

    with pytest.raises(SystemExit, match="already contains a completion timestamp"):
        start_main()

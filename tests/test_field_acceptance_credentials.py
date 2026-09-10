import importlib.util
from pathlib import Path


FIELD_ACCEPTANCE = Path(__file__).parents[1] / "tools" / "field_acceptance.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("field_acceptance", FIELD_ACCEPTANCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_password_argument_is_rejected(monkeypatch, tmp_path):
    module = _load_module()
    monkeypatch.setattr(module, "_run", lambda command: (_ for _ in ()).throw(
        AssertionError("subprocess must not run when a password is supplied on argv")
    ))

    try:
        module.main(["http://bridge", str(tmp_path), "--username", "operator", "--password", "secret"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("--password must be rejected")


def test_password_env_is_forwarded_without_secret_in_command(monkeypatch, tmp_path):
    module = _load_module()
    monkeypatch.setenv("NAVIC_TEST_PASSWORD", "secret-value")
    commands = []

    def fake_run(command):
        commands.append(command)
        if "live_acceptance.py" in " ".join(command):
            return 1, ""
        return 1, ""

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_load", lambda path: {"passed": False, "failures": ["test"]})

    rc = module.main([
        "http://bridge", str(tmp_path), "--duration", "1",
        "--username", "operator", "--password-env", "NAVIC_TEST_PASSWORD",
    ])

    assert rc == 1
    live_commands = [command for command in commands if "live_acceptance.py" in " ".join(command)]
    assert len(live_commands) == 1
    command = live_commands[0]
    assert "--password" not in command
    assert "secret-value" not in command
    assert command[-1] == "NAVIC_TEST_PASSWORD"

import importlib.util
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
SCAFFOLD = TOOLS_DIR / "create_hardware_qualification_run.py"


def _load_module():
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        spec = importlib.util.spec_from_file_location("create_hardware_qualification_run", SCAFFOLD)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def test_metadata_text_rejects_control_characters():
    module = _load_module()

    for value in ("receiver\nmodel", "board\rrev", "operator\x00name"):
        try:
            module.validate_metadata_text("receiver", value)
        except SystemExit as exc:
            assert "control characters" in str(exc)
        else:
            raise AssertionError("control characters must be rejected")


def test_metadata_text_allows_human_readable_values():
    module = _load_module()

    module.validate_metadata_text("receiver", "u-blox M10 / custom antenna")
    module.validate_metadata_text("operator", "Field Operator 01")
    module.validate_metadata_text("board", "ESP32-S3 DevKitC-1")


def test_metadata_text_rejects_overlong_values():
    module = _load_module()

    try:
        module.validate_metadata_text("receiver", "x" * 201)
    except SystemExit as exc:
        assert "200 characters" in str(exc)
    else:
        raise AssertionError("overlong metadata must be rejected")

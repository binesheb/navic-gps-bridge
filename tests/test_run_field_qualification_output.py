import pytest

from tools.run_field_qualification import run


def test_rejects_output_directory_equal_to_bundle(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    with pytest.raises(ValueError, match="outside the evidence bundle"):
        run(bundle, bundle)


def test_rejects_output_directory_inside_bundle(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    with pytest.raises(ValueError, match="outside the evidence bundle"):
        run(bundle, bundle / "qualification-output")


def test_allows_output_directory_sibling_to_bundle(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    output = tmp_path / "qualification-output"
    bundle.mkdir()

    def fail_if_reached(*args, **kwargs):
        raise RuntimeError("guard passed")

    monkeypatch.setattr("tools.run_field_qualification.validate_manifest", fail_if_reached)
    with pytest.raises(RuntimeError, match="guard passed"):
        run(bundle, output)
    assert output.is_dir()

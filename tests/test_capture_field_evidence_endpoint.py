import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "capture_field_evidence.py"
spec = importlib.util.spec_from_file_location("capture_field_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_parse_bridge_host_hostname():
    assert module.parse_bridge_host("http://bridge.local:8080") == "bridge.local"


def test_parse_bridge_host_ipv4():
    assert module.parse_bridge_host("http://127.0.0.1:8080") == "127.0.0.1"


def test_parse_bridge_host_ipv6():
    assert module.parse_bridge_host("http://[::1]:8080") == "::1"


def test_parse_bridge_host_ipv6_zone_identifier():
    assert module.parse_bridge_host("http://[fe80::1234%25eth0]:8080") == "fe80::1234%eth0"


def test_parse_bridge_host_rejects_hostless_url():
    try:
        module.parse_bridge_host("http:///api")
    except ValueError as exc:
        assert str(exc) == "bridge URL must contain a hostname"
    else:
        raise AssertionError("expected ValueError")


def test_parse_bridge_host_rejects_unsupported_scheme():
    try:
        module.parse_bridge_host("ftp://bridge.local:8080")
    except ValueError as exc:
        assert str(exc) == "bridge URL must use http or https"
    else:
        raise AssertionError("expected ValueError")

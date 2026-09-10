import pytest

from tools.field_acceptance import _nmea_host


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://192.0.2.10", "192.0.2.10"),
        ("https://bridge.example.test:8443/path", "bridge.example.test"),
        ("http://[2001:db8::10]:8080", "2001:db8::10"),
        ("http://[fe80::10%25eth0]:8080", "fe80::10%eth0"),
    ],
)
def test_nmea_host_supports_ipv4_hostname_and_ipv6(url, expected):
    assert _nmea_host(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "192.0.2.10:8080",
        "ftp://192.0.2.10",
        "http:///missing-host",
        "http://[broken",
    ],
)
def test_nmea_host_rejects_invalid_endpoint(url):
    with pytest.raises(ValueError):
        _nmea_host(url)

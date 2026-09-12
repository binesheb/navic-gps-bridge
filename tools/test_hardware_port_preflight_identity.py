from hardware_port_preflight import identity_failures


def test_identity_expectations_accept_exact_match():
    identity = {
        "vid": 0x10C4,
        "pid": 0xEA60,
        "serial_number": "GNSS-001",
        "manufacturer": "Silicon Labs",
        "product": "CP210x USB to UART Bridge",
    }
    assert identity_failures(
        identity,
        0x10C4,
        0xEA60,
        "GNSS-001",
        "Silicon Labs",
        "CP210x USB to UART Bridge",
    ) == []


def test_identity_expectations_fail_closed_on_serial_number():
    identity = {
        "vid": 0x10C4,
        "pid": 0xEA60,
        "serial_number": "OTHER",
        "manufacturer": "Silicon Labs",
        "product": "CP210x USB to UART Bridge",
    }
    failures = identity_failures(identity, 0x10C4, 0xEA60, "GNSS-001")
    assert failures == ["FAIL: serial number 'OTHER' != expected 'GNSS-001'"]


def test_identity_expectations_fail_closed_on_missing_metadata():
    identity = {"vid": 0x10C4, "pid": 0xEA60}
    failures = identity_failures(identity, None, None, "GNSS-001", "Silicon Labs", "CP210x USB to UART Bridge")
    assert len(failures) == 3
    assert "serial number None" in failures[0]
    assert "manufacturer None" in failures[1]
    assert "product None" in failures[2]

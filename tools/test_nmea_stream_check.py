#!/usr/bin/env python3
"""Self-test for the dependency-free live NMEA checker."""

from collections import Counter

from nmea_stream_check import build_report, checksum_ok, sentence_kind


def test_known_valid_sentence() -> None:
    assert checksum_ok("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A")


def test_bad_checksum_is_rejected() -> None:
    assert not checksum_ok("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*00")


def test_malformed_sentence_is_rejected() -> None:
    assert not checksum_ok("GPRMC,123519,A*00")
    assert not checksum_ok("$GPRMC,123519,A*0")
    assert not checksum_ok("$GPRMC,123519,A*6Aextra")


def test_sentence_kind_extracts_talker_and_type() -> None:
    assert sentence_kind("$GPRMC,123519,A*6A") == "GPRMC"
    assert sentence_kind("$GNGGA,123519,4807.038,N*00") == "GNGGA"


def test_sentence_kind_rejects_malformed_prefix() -> None:
    assert sentence_kind("GPRMC,123519,A*6A") is None
    assert sentence_kind("$GP,123519,A*00") is None


def test_report_passes_required_types_and_minimum() -> None:
    report, failures = build_report(
        10, 0, Counter({"GPRMC": 6, "GPGGA": 4}), Counter({"GP": 10}),
        30.0, 10, 100.0, ["GPRMC", "GPGGA"],
    )
    assert report["passed"] is True
    assert report["valid_percent"] == 100.0
    assert failures == []


def test_report_rejects_missing_required_type() -> None:
    report, failures = build_report(
        10, 0, Counter({"GPRMC": 10}), Counter({"GP": 10}),
        30.0, 1, 100.0, ["GPRMC", "GPGGA"],
    )
    assert report["passed"] is False
    assert any("GPGGA" in failure for failure in failures)


def test_report_rejects_invalid_checksum() -> None:
    report, failures = build_report(
        9, 1, Counter({"GPRMC": 9}), Counter({"GP": 9}),
        30.0, 1, 90.0, [],
    )
    assert report["passed"] is False
    assert report["invalid_sentences"] == 1
    assert any("checksum" in failure for failure in failures)


def test_report_rejects_low_valid_percentage() -> None:
    report, failures = build_report(
        8, 2, Counter({"GPRMC": 8}), Counter({"GP": 8}),
        30.0, 1, 90.0, [],
    )
    assert report["valid_percent"] == 80.0
    assert report["passed"] is False
    assert any("percentage" in failure for failure in failures)


def test_report_accepts_configured_validity_threshold() -> None:
    report, failures = build_report(
        9, 1, Counter({"GPRMC": 9}), Counter({"GP": 9}),
        30.0, 1, 90.0, [],
    )
    assert report["passed"] is True
    assert failures == []


if __name__ == "__main__":
    test_known_valid_sentence()
    test_bad_checksum_is_rejected()
    test_malformed_sentence_is_rejected()
    test_sentence_kind_extracts_talker_and_type()
    test_sentence_kind_rejects_malformed_prefix()
    test_report_passes_required_types_and_minimum()
    test_report_rejects_missing_required_type()
    test_report_rejects_invalid_checksum()
    test_report_rejects_low_valid_percentage()
    test_report_accepts_configured_validity_threshold()
    print("PASS: nmea_stream_check self-tests")

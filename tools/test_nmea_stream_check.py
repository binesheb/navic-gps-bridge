#!/usr/bin/env python3
"""Self-test for the dependency-free live NMEA checker."""

from nmea_stream_check import checksum_ok, sentence_kind


def test_known_valid_sentence() -> None:
    assert checksum_ok("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A")


def test_bad_checksum_is_rejected() -> None:
    assert not checksum_ok("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*00")


def test_malformed_sentence_is_rejected() -> None:
    assert not checksum_ok("GPRMC,123519,A*00")
    assert not checksum_ok("$GPRMC,123519,A*0")


def test_sentence_kind_extracts_talker_and_type() -> None:
    assert sentence_kind("$GPRMC,123519,A*6A") == "GPRMC"
    assert sentence_kind("$GNGGA,123519,4807.038,N*00") == "GNGGA"


def test_sentence_kind_rejects_malformed_prefix() -> None:
    assert sentence_kind("GPRMC,123519,A*6A") is None
    assert sentence_kind("$GP,123519,A*00") is None


if __name__ == "__main__":
    test_known_valid_sentence()
    test_bad_checksum_is_rejected()
    test_malformed_sentence_is_rejected()
    test_sentence_kind_extracts_talker_and_type()
    test_sentence_kind_rejects_malformed_prefix()
    print("PASS: nmea_stream_check self-tests")

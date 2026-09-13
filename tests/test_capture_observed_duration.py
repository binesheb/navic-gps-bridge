from tools.capture_field_evidence import calculate_observed_duration


def test_observed_duration_uses_monotonic_elapsed_time():
    # Wall-clock adjustments cannot affect the duration calculation because
    # capture elapsed time comes from a monotonic clock.
    assert calculate_observed_duration(100.0, 112.75) == 12.75


def test_observed_duration_never_goes_negative():
    assert calculate_observed_duration(112.75, 100.0) == 0.0

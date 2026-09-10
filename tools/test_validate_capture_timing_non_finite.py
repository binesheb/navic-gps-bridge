from pathlib import Path

import pytest

from tools.validate_capture_timing import _validate_sequence


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_validate_sequence_rejects_non_finite_elapsed_time(value: float) -> None:
    with pytest.raises(ValueError, match="timing record 2 is not finite"):
        _validate_sequence("live.csv", [0.0, value], 10.0)


def test_validate_sequence_accepts_finite_monotonic_values() -> None:
    _validate_sequence("live.csv", [0.0, 0.5, 1.0], 10.0)

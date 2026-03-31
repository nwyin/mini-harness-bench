"""Hidden tests for test-oracle-mismatch task."""

import os
import sys
from pathlib import Path


def _workspace():
    pp = os.environ.get("PYTHONPATH")
    if pp:
        return Path(pp)
    return Path(__file__).resolve().parent.parent / "workspace"


def _setup():
    ws = str(_workspace())
    if ws not in sys.path:
        sys.path.insert(0, ws)


def _cleanup():
    for mod_name in list(sys.modules):
        if mod_name in ("analytics",):
            del sys.modules[mod_name]


def test_moving_average_correct():
    """moving_average produces correct values after fix."""
    _setup()
    try:
        from analytics import moving_average

        result = moving_average([1, 2, 3, 4, 5], 3)
        expected = [1.0, 1.5, 2.0, 3.0, 4.0]
        assert len(result) == len(expected)
        for r, e in zip(result, expected):
            assert abs(r - e) < 1e-9, f"Expected {e}, got {r}"
    finally:
        _cleanup()


def test_moving_average_window_one():
    """Window of 1 should return the data itself."""
    _setup()
    try:
        from analytics import moving_average

        result = moving_average([5, 10, 15], 1)
        expected = [5.0, 10.0, 15.0]
        for r, e in zip(result, expected):
            assert abs(r - e) < 1e-9, f"Expected {e}, got {r}"
    finally:
        _cleanup()


def test_weighted_mean_correct():
    """weighted_mean matches hand-computed values."""
    _setup()
    try:
        from analytics import weighted_mean

        # (10*1 + 20*2 + 30*3) / (1+2+3) = 140/6 = 23.333...
        result = weighted_mean([10, 20, 30], [1, 2, 3])
        assert abs(result - 23.333333333333332) < 1e-9, f"Expected ~23.33, got {result}"
    finally:
        _cleanup()


def test_correlation_allows_negative():
    """Negative correlation returns a float, not an exception."""
    _setup()
    try:
        from analytics import correlation

        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        result = correlation(x, y)
        assert isinstance(result, float), f"Expected float, got {type(result)}"
        assert abs(result - (-1.0)) < 1e-9, f"Expected -1.0, got {result}"
    finally:
        _cleanup()


def test_moving_average_larger_window():
    """moving_average with window larger than data uses available elements."""
    _setup()
    try:
        from analytics import moving_average

        result = moving_average([10, 20, 30], 5)
        # Window 5 but only 3 elements, so all use data[0:i+1]
        expected = [10.0, 15.0, 20.0]
        assert len(result) == len(expected)
        for r, e in zip(result, expected):
            assert abs(r - e) < 1e-9, f"Expected {e}, got {r}"
    finally:
        _cleanup()


def test_moving_average_single_element():
    """moving_average with single element."""
    _setup()
    try:
        from analytics import moving_average

        result = moving_average([42], 3)
        assert len(result) == 1
        assert abs(result[0] - 42.0) < 1e-9
    finally:
        _cleanup()


def test_correlation_uncorrelated():
    """Near-zero correlation for uncorrelated data."""
    _setup()
    try:
        from analytics import correlation

        # Manually constructed to have near-zero correlation
        x = [1, 2, 3, 4, 5]
        y = [3, 1, 4, 2, 5]
        result = correlation(x, y)
        # Should return a float (not raise), value around 0.5
        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0
    finally:
        _cleanup()

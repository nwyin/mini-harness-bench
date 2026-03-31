"""Tests for analytics module.

Note: some of these tests may themselves contain bugs.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytics import correlation, moving_average, normalize, percentile, weighted_mean


def test_weighted_mean():
    """Test weighted mean computation."""
    values = [10, 20, 30]
    weights = [1, 2, 3]
    # Hand computation: (10*1 + 20*2 + 30*3) / (1 + 2 + 3) = 140 / 6 = 23.333...
    # BUG IN TEST: wrong expected value (computed as 140/5 = 28.0,
    # as if weight sum were 5 instead of 6)
    result = weighted_mean(values, weights)
    assert abs(result - 28.0) < 1e-9, f"Expected ~28.0, got {result}"


def test_weighted_mean_equal_weights():
    """Equal weights should give the regular mean."""
    values = [4, 8, 12]
    weights = [1, 1, 1]
    result = weighted_mean(values, weights)
    assert abs(result - 8.0) < 1e-9


def test_percentile_median():
    """50th percentile of sorted data."""
    data = [1, 2, 3, 4, 5]
    result = percentile(data, 50)
    assert abs(result - 3.0) < 1e-9


def test_percentile_boundaries():
    """0th and 100th percentile."""
    data = [10, 20, 30, 40, 50]
    assert percentile(data, 0) == 10
    assert percentile(data, 100) == 50


def test_moving_average_basic():
    """Basic moving average with window 3."""
    data = [1, 2, 3, 4, 5]
    result = moving_average(data, 3)
    # Expected: [1.0, 1.5, 2.0, 3.0, 4.0]
    expected = [1.0, 1.5, 2.0, 3.0, 4.0]
    assert len(result) == len(expected)
    for r, e in zip(result, expected):
        assert abs(r - e) < 1e-9, f"Expected {e}, got {r}"


def test_moving_average_window_one():
    """Window of 1 should return the data itself."""
    data = [5, 10, 15]
    result = moving_average(data, 1)
    expected = [5.0, 10.0, 15.0]
    for r, e in zip(result, expected):
        assert abs(r - e) < 1e-9


def test_correlation_positive():
    """Perfectly correlated data should give correlation of 1.0."""
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    result = correlation(x, y)
    assert abs(result - 1.0) < 1e-9


def test_correlation_negative():
    """Negatively correlated data."""
    x = [1, 2, 3, 4, 5]
    y = [10, 8, 6, 4, 2]
    # BUG IN TEST: correlation() returns -1.0 for perfectly negatively
    # correlated data; it should NOT raise ValueError.
    # The test incorrectly expects an exception.
    with pytest.raises(ValueError):
        correlation(x, y)


def test_normalize():
    """Normalize maps min to 0 and max to 1."""
    data = [10, 20, 30, 40, 50]
    result = normalize(data)
    assert result[0] == 0.0
    assert result[-1] == 1.0
    assert abs(result[2] - 0.5) < 1e-9

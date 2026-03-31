"""Statistical analytics functions.

Each function has a clear docstring describing its expected behavior.
"""

from __future__ import annotations


def weighted_mean(values: list[float], weights: list[float]) -> float:
    """Compute the weighted mean of values.

    weighted_mean = sum(v_i * w_i) / sum(w_i)

    Raises ValueError if values and weights have different lengths or if
    all weights are zero.
    """
    if len(values) != len(weights):
        raise ValueError("values and weights must have the same length")
    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("total weight must be non-zero")
    return sum(v * w for v, w in zip(values, weights)) / total_weight


def percentile(data: list[float], p: float) -> float:
    """Compute the p-th percentile of data using linear interpolation.

    p should be between 0 and 100. Uses the 'exclusive' method:
    rank = (p / 100) * (n + 1), then interpolate between adjacent values.
    Clamps to first/last element if rank is out of bounds.
    """
    if not data:
        raise ValueError("data must not be empty")
    if not (0 <= p <= 100):
        raise ValueError("p must be between 0 and 100")
    sorted_data = sorted(data)
    n = len(sorted_data)
    rank = (p / 100) * (n + 1)
    if rank <= 1:
        return sorted_data[0]
    if rank >= n:
        return sorted_data[-1]
    lower = int(rank) - 1
    frac = rank - int(rank)
    return sorted_data[lower] + frac * (sorted_data[lower + 1] - sorted_data[lower])


def moving_average(data: list[float], window: int) -> list[float]:
    """Compute the moving average with the given window size.

    Returns a list where element i is the mean of data[i-window+1 : i+1].
    For the first (window-1) elements where the full window is not available,
    use whatever elements are available (i.e., data[0 : i+1]).

    Example: moving_average([1, 2, 3, 4, 5], 3)
    -> [1.0, 1.5, 2.0, 3.0, 4.0]
    """
    if window <= 0:
        raise ValueError("window must be positive")
    result = []
    for i in range(len(data)):
        # FIX: use i - window + 1 (not i - window)
        start = max(0, i - window + 1)
        chunk = data[start : i + 1]
        result.append(sum(chunk) / len(chunk))
    return result


def correlation(x: list[float], y: list[float]) -> float:
    """Compute Pearson correlation coefficient between x and y.

    Returns a float between -1 and 1. Raises ValueError if lengths differ
    or if either series has zero variance.
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    n = len(x)
    if n < 2:
        raise ValueError("need at least 2 data points")
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)
    if var_x == 0 or var_y == 0:
        raise ValueError("zero variance in input")
    return cov / (var_x * var_y) ** 0.5

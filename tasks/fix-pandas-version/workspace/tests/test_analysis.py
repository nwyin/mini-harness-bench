"""Tests for the pandas analysis module."""

import sys
from pathlib import Path

# Add workspace to path so analysis.py can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis import (
    add_summary_row,
    build_sales_dataframe,
    calculate_net_sales,
    check_monotonic,
    column_summary,
    full_analysis,
    swap_multi_index_levels,
)


def test_build_dataframe():
    df = build_sales_dataframe()
    assert len(df) == 4
    assert list(df.columns) == ["product", "region", "sales", "returns"]


def test_add_summary_row():
    df = build_sales_dataframe()
    result = add_summary_row(df)
    assert len(result) == 5
    assert result.iloc[-1]["product"] == "TOTAL"
    assert result.iloc[-1]["sales"] == 570  # 100 + 150 + 200 + 120


def test_calculate_net_sales():
    df = build_sales_dataframe()
    result = calculate_net_sales(df)
    assert "net_sales" in result.columns
    assert "net_sales_sqrt" in result.columns
    assert result.iloc[0]["net_sales"] == 95  # 100 - 5


def test_swap_index():
    df = build_sales_dataframe()
    result = swap_multi_index_levels(df)
    assert list(result.index.names) == ["product", "region"]


def test_check_monotonic():
    import pandas as pd

    s = pd.Series([1, 2, 3, 4])
    assert check_monotonic(s) is True

    s2 = pd.Series([1, 3, 2, 4])
    assert check_monotonic(s2) is False


def test_column_summary():
    df = build_sales_dataframe()
    summary = column_summary(df)
    assert "product" in summary
    assert "sales" in summary
    assert len(summary) == 4


def test_full_analysis():
    result = full_analysis()
    assert result["row_count"] == 5
    assert result["has_total_row"] is True
    assert result["net_sales_col_exists"] is True
    assert result["sqrt_col_exists"] is True
    assert result["swapped_index_names"] == ["product", "region"]
    assert result["is_sorted_monotonic"] is True
    assert len(result["column_types"]) == 4

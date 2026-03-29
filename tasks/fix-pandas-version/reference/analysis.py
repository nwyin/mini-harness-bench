"""Data analysis module using pandas.

Updated to work with pandas >= 2.0.
"""

import numpy as np
import pandas as pd


def build_sales_dataframe() -> pd.DataFrame:
    """Create a sample sales DataFrame."""
    return pd.DataFrame(
        {
            "product": ["Widget", "Gadget", "Doohickey", "Thingamajig"],
            "region": ["North", "South", "North", "South"],
            "sales": [100, 150, 200, 120],
            "returns": [5, 10, 8, 3],
        }
    )


def add_summary_row(df: pd.DataFrame) -> pd.DataFrame:
    """Add a summary row with totals to the DataFrame."""
    summary = pd.DataFrame(
        {
            "product": ["TOTAL"],
            "region": ["ALL"],
            "sales": [df["sales"].sum()],
            "returns": [df["returns"].sum()],
        }
    )
    return pd.concat([df, summary], ignore_index=True)


def calculate_net_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate net sales using numpy."""
    df = df.copy()
    df["net_sales"] = df["sales"] - df["returns"]
    df["net_sales_sqrt"] = np.sqrt(df["net_sales"].values.astype(float))
    return df


def swap_multi_index_levels(df: pd.DataFrame) -> pd.DataFrame:
    """Create a multi-index DataFrame and swap levels."""
    indexed = df.set_index(["region", "product"])
    return indexed.swaplevel(i=0, j=1)


def check_monotonic(series: pd.Series) -> bool:
    """Check if a series is monotonically increasing."""
    return series.is_monotonic_increasing


def column_summary(df: pd.DataFrame) -> dict[str, str]:
    """Return a summary of each column's dtype."""
    summary = {}
    for col_name, col_data in df.items():
        summary[col_name] = str(col_data.dtype)
    return summary


def full_analysis() -> dict:
    """Run the full analysis pipeline."""
    df = build_sales_dataframe()
    df_net = calculate_net_sales(df)
    df_with_total = add_summary_row(df_net)
    swapped = swap_multi_index_levels(df)
    sales_sorted = df["sales"].sort_values()
    is_mono = check_monotonic(sales_sorted)
    col_types = column_summary(df)

    return {
        "row_count": len(df_with_total),
        "has_total_row": df_with_total.iloc[-1]["product"] == "TOTAL",
        "net_sales_col_exists": "net_sales" in df_net.columns,
        "sqrt_col_exists": "net_sales_sqrt" in df_net.columns,
        "swapped_index_names": list(swapped.index.names),
        "is_sorted_monotonic": is_mono,
        "column_types": col_types,
    }

#!/usr/bin/env python3
"""Convert CSV to Parquet format with correct column types."""

import pandas as pd


def main():
    df = pd.read_csv("data.csv")

    df["id"] = df["id"].astype(int)
    df["name"] = df["name"].astype(str)
    df["department"] = df["department"].astype(str)
    df["salary"] = df["salary"].astype(float)
    df["start_date"] = pd.to_datetime(df["start_date"])

    df.to_parquet("output.parquet", engine="pyarrow", index=False)


if __name__ == "__main__":
    main()

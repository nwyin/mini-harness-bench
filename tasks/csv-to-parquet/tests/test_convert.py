import os
import subprocess
import sys

import pandas as pd
import pyarrow.parquet as pq
import pytest


@pytest.fixture(autouse=True)
def run_convert():
    """Run the conversion script before tests."""
    result = subprocess.run([sys.executable, "convert.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"convert.py failed: {result.stderr}"


def test_output_exists():
    assert os.path.exists("output.parquet")


def test_row_count():
    df = pd.read_parquet("output.parquet")
    assert len(df) == 20


def test_column_names():
    df = pd.read_parquet("output.parquet")
    assert list(df.columns) == ["id", "name", "department", "salary", "start_date"]


def test_id_column_type():
    table = pq.read_table("output.parquet")
    id_type = table.schema.field("id").type
    assert "int" in str(id_type).lower(), f"Expected int type for id, got {id_type}"


def test_salary_column_type():
    table = pq.read_table("output.parquet")
    salary_type = table.schema.field("salary").type
    assert "double" in str(salary_type).lower() or "float" in str(salary_type).lower(), f"Expected float type for salary, got {salary_type}"


def test_start_date_column_type():
    table = pq.read_table("output.parquet")
    date_type = table.schema.field("start_date").type
    assert "timestamp" in str(date_type).lower(), f"Expected timestamp type for start_date, got {date_type}"


def test_data_integrity():
    """Verify specific values survived the conversion."""
    df = pd.read_parquet("output.parquet")
    alice = df[df["name"] == "Alice Johnson"].iloc[0]
    assert alice["id"] == 1
    assert alice["department"] == "Engineering"
    assert abs(alice["salary"] - 95000.00) < 0.01


def test_all_departments_present():
    df = pd.read_parquet("output.parquet")
    assert set(df["department"].unique()) == {"Engineering", "Marketing", "Sales"}

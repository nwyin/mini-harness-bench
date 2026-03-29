import csv
import os
import subprocess
import sys

import pytest


@pytest.fixture(autouse=True)
def run_etl():
    """Run the ETL script before tests."""
    result = subprocess.run([sys.executable, "etl.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"etl.py failed: {result.stderr}"


def load_output():
    with open("output.csv") as f:
        reader = csv.DictReader(f)
        return list(reader)


def test_output_exists():
    assert os.path.exists("output.csv")


def test_has_header_columns():
    rows = load_output()
    assert len(rows) > 0
    assert set(rows[0].keys()) == {"category", "total_revenue", "num_orders", "avg_price"}


def test_correct_categories():
    rows = load_output()
    categories = [r["category"] for r in rows]
    assert set(categories) == {"electronics", "books", "clothing"}


def test_filtered_zero_quantity():
    """clothing row with quantity=0 should be excluded from aggregation."""
    rows = load_output()
    clothing = [r for r in rows if r["category"] == "clothing"]
    assert len(clothing) == 1
    # Only orders 6 (49.99*2=99.98) and 9 (34.99*3=104.97) count
    assert int(clothing[0]["num_orders"]) == 2


def test_filtered_negative_quantity():
    """electronics row with quantity=-1 should be excluded."""
    rows = load_output()
    elec = [r for r in rows if r["category"] == "electronics"]
    assert len(elec) == 1
    # Orders 1 (99.99*2=199.98), 3 (149.99*1=149.99), 10 (79.99*4=319.96)
    assert int(elec[0]["num_orders"]) == 3


def test_sorted_by_revenue_desc():
    rows = load_output()
    revenues = [float(r["total_revenue"]) for r in rows]
    assert revenues == sorted(revenues, reverse=True)


def test_electronics_revenue():
    rows = load_output()
    elec = [r for r in rows if r["category"] == "electronics"][0]
    # 99.99*2 + 149.99*1 + 79.99*4 = 199.98 + 149.99 + 319.96 = 669.93
    assert abs(float(elec["total_revenue"]) - 669.93) < 0.01

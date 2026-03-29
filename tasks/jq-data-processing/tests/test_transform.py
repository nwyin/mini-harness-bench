import json
import os
import subprocess
import sys

import pytest


@pytest.fixture(autouse=True)
def run_transform():
    """Run transform.py before tests."""
    result = subprocess.run([sys.executable, "transform.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"transform.py failed: {result.stderr}"


def load_output():
    with open("output.json") as f:
        return json.load(f)


def test_output_exists():
    assert os.path.exists("output.json")


def test_has_summary_key():
    data = load_output()
    assert "summary" in data
    assert isinstance(data["summary"], list)
    assert len(data["summary"]) == 5


def test_summary_sorted_by_total_spent():
    data = load_output()
    totals = [u["total_spent"] for u in data["summary"]]
    assert totals == sorted(totals, reverse=True)


def test_alice_total_spent():
    data = load_output()
    alice = [u for u in data["summary"] if u["name"] == "Alice Johnson"][0]
    # 1299.99 + 29.99 + 79.99 = 1409.97
    assert abs(alice["total_spent"] - 1409.97) < 0.01
    assert alice["order_count"] == 3


def test_alice_most_expensive():
    data = load_output()
    alice = [u for u in data["summary"] if u["name"] == "Alice Johnson"][0]
    assert alice["most_expensive_order"]["product"] == "Laptop"
    assert abs(alice["most_expensive_order"]["amount"] - 1299.99) < 0.01


def test_total_revenue():
    data = load_output()
    # Alice: 1409.97, Bob: 589.98, Carol: 1185.96, David: 199.99, Eve: 514.97
    expected = 1409.97 + 589.98 + 1185.96 + 199.99 + 514.97
    assert abs(data["total_revenue"] - expected) < 0.01


def test_top_spender():
    data = load_output()
    assert data["top_spender"] == "Alice Johnson"


def test_user_entry_structure():
    data = load_output()
    for entry in data["summary"]:
        assert "user_id" in entry
        assert "name" in entry
        assert "email" in entry
        assert "total_spent" in entry
        assert "order_count" in entry
        assert "most_expensive_order" in entry
        meo = entry["most_expensive_order"]
        assert "order_id" in meo
        assert "amount" in meo
        assert "product" in meo

import os
import subprocess
import sys


def setup_module():
    result = subprocess.run([sys.executable, "normalize.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"normalize.py failed: {result.stderr}"


def load_output():
    with open("output.txt") as f:
        return [line.strip() for line in f if line.strip()]


def test_output_exists():
    assert os.path.exists("output.txt")


def test_correct_count():
    lines = load_output()
    assert len(lines) == 10


def test_us_format():
    """03/15/2024 -> 2024-03-15"""
    lines = load_output()
    assert lines[0] == "2024-03-15"


def test_dmy_format():
    """15-Mar-2024 -> 2024-03-15"""
    lines = load_output()
    assert lines[1] == "2024-03-15"


def test_long_format():
    """March 15, 2024 -> 2024-03-15"""
    lines = load_output()
    assert lines[2] == "2024-03-15"


def test_dotted_format():
    """2024.03.15 -> 2024-03-15"""
    lines = load_output()
    assert lines[3] == "2024-03-15"


def test_european_format():
    """25/12/2023 -> 2023-12-25 (day > 12 implies DD/MM/YYYY)"""
    lines = load_output()
    assert lines[4] == "2023-12-25"


def test_ambiguous_us_format():
    """01/07/2024 -> 2024-01-07 (day <= 12, treat as MM/DD/YYYY)"""
    lines = load_output()
    assert lines[5] == "2024-01-07"


def test_july_4():
    """July 4, 2024 -> 2024-07-04"""
    lines = load_output()
    assert lines[6] == "2024-07-04"


def test_feb_28():
    """28/02/2023 -> 2023-02-28"""
    lines = load_output()
    assert lines[9] == "2023-02-28"


def test_all_iso_format():
    """All output lines should match YYYY-MM-DD pattern."""
    import re

    lines = load_output()
    for line in lines:
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", line), f"Not ISO format: {line}"

"""Basic tests for the CSV processing app."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_output_matches_expected():
    """Run the app and compare output to expected_output.csv."""
    ws = Path(__file__).resolve().parent.parent
    input_path = ws / "failing_input.csv"
    expected_path = ws / "expected_output.csv"
    config_path = ws / "config.yaml"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        from app import process

        process(str(input_path), tmp_path, str(config_path))

        with open(tmp_path) as f:
            actual = f.read().strip()
        with open(expected_path) as f:
            expected = f.read().strip()

        assert actual == expected, f"Output does not match expected.\nActual:\n{actual}\nExpected:\n{expected}"
    finally:
        os.unlink(tmp_path)

"""Hidden tests for config-aware-bugfix task."""

import hashlib
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def _workspace():
    pp = os.environ.get("PYTHONPATH")
    if pp:
        return Path(pp)
    return Path(__file__).resolve().parent.parent / "workspace"


def _workspace_dir():
    """Always returns the actual workspace directory."""
    return Path(__file__).resolve().parent.parent / "workspace"


def _setup():
    ws = str(_workspace())
    if ws not in sys.path:
        sys.path.insert(0, ws)


def _cleanup():
    for mod_name in list(sys.modules):
        if mod_name in ("app", "transforms", "validators"):
            del sys.modules[mod_name]


def test_output_matches_expected():
    """Run app and compare output to expected_output.csv."""
    _setup()
    try:
        ws = _workspace()
        from app import process

        input_path = _workspace_dir() / "failing_input.csv"
        expected_path = _workspace_dir() / "expected_output.csv"
        config_path = ws / "config.yaml"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            process(str(input_path), tmp_path, str(config_path))

            with open(tmp_path) as f:
                actual = f.read().strip()
            with open(expected_path) as f:
                expected = f.read().strip()

            assert actual == expected, f"Output does not match expected.\nActual:\n{actual}\n\nExpected:\n{expected}"
        finally:
            os.unlink(tmp_path)
    finally:
        _cleanup()


def test_date_parsing_correct():
    """Specific dates are parsed to correct month/day."""
    _setup()
    try:
        import yaml

        ws = _workspace()
        config_path = ws / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        date_format = config["transforms"]["date_format"]

        # 2024-05-03 should be May 3, not March 5
        dt = datetime.strptime("2024-05-03", date_format)
        assert dt.month == 5, f"Expected month=5 (May), got month={dt.month}"
        assert dt.day == 3, f"Expected day=3, got day={dt.day}"

        # 2024-11-08 should be November 8, not August 11
        dt2 = datetime.strptime("2024-11-08", date_format)
        assert dt2.month == 11, f"Expected month=11, got month={dt2.month}"
        assert dt2.day == 8, f"Expected day=8, got day={dt2.day}"
    finally:
        _cleanup()


def test_config_format_string():
    """config.yaml must have the correct date format string."""
    _setup()
    try:
        import yaml

        ws = _workspace()
        config_path = ws / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        fmt = config["transforms"]["date_format"]
        assert fmt == "%Y-%m-%d", f"Expected date_format='%Y-%m-%d', got '{fmt}'"
    finally:
        _cleanup()


def test_code_unchanged():
    """app.py, transforms.py, validators.py should NOT be modified."""
    ws = _workspace_dir()

    expected_hashes = {
        "app.py": "57f14bd8b7486653f261b5de82279d68568ba20376e848fb58ab7e0bcae00b4b",
        "transforms.py": "7b73356331ae238d2016f0e1c74c108b1469c44e02035d4e2b54cdbd25895c64",
        "validators.py": "1fcb54fd315966f105b365b0cea4ee27506196f9e4abcecf9f58e840faa802fb",
    }

    for filename, expected_hash in expected_hashes.items():
        filepath = ws / filename
        assert filepath.exists(), f"{filename} is missing"
        with open(filepath, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        assert actual_hash == expected_hash, f"{filename} was modified but should not have been. The bug is in config.yaml, not in the code."


def test_january_dates():
    """Dates in January parse correctly."""
    _setup()
    try:
        import yaml

        ws = _workspace()
        config_path = ws / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        date_format = config["transforms"]["date_format"]
        dt = datetime.strptime("2024-01-15", date_format)
        assert dt.month == 1, f"Expected month=1, got {dt.month}"
        assert dt.day == 15, f"Expected day=15, got {dt.day}"
    finally:
        _cleanup()


def test_december_dates():
    """Dates in December parse correctly."""
    _setup()
    try:
        import yaml

        ws = _workspace()
        config_path = ws / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        date_format = config["transforms"]["date_format"]
        dt = datetime.strptime("2024-12-25", date_format)
        assert dt.month == 12, f"Expected month=12, got {dt.month}"
        assert dt.day == 25, f"Expected day=25, got {dt.day}"
    finally:
        _cleanup()

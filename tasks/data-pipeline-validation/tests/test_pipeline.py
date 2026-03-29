"""Tests for data-pipeline-validation task."""

import os
import sys
import tempfile
from pathlib import Path

_pp = os.environ.get("PYTHONPATH")
WORKSPACE = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"
_task_dir = os.environ.get("MHB_TASK_DIR")
TEST_DATA = Path(_task_dir) / "tests" / "data" if _task_dir else Path(__file__).resolve().parent / "data"


def _setup():
    ws = str(WORKSPACE)
    if ws not in sys.path:
        sys.path.insert(0, ws)


def _cleanup():
    for mod_name in list(sys.modules):
        if mod_name == "pipeline":
            del sys.modules[mod_name]


def test_read_csv_basic():
    """Read the workspace example CSV."""
    _setup()
    try:
        from pipeline import read_csv

        rows = read_csv(str(WORKSPACE / "example.csv"))
        assert len(rows) == 4
        assert rows[0]["name"] == "Alice"
        assert rows[0]["age"] == "30"
    finally:
        _cleanup()


def test_read_csv_empty():
    """Reading a CSV with only headers returns empty list."""
    _setup()
    try:
        from pipeline import read_csv

        rows = read_csv(str(TEST_DATA / "empty.csv"))
        assert rows == []
    finally:
        _cleanup()


def test_validate_schema_with_errors():
    """Schema validation catches type errors and missing columns."""
    _setup()
    try:
        from pipeline import read_csv, validate_schema

        rows = read_csv(str(TEST_DATA / "employees.csv"))
        schema = {"name": "str", "age": "int", "salary": "float", "active": "bool"}
        valid, errors = validate_schema(rows, schema)

        # Charlie has non-numeric age, Eve has empty age, Frank has invalid salary
        assert len(errors) >= 3
        # Alice, Bob, Diana should be valid (at minimum)
        assert len(valid) >= 3
    finally:
        _cleanup()


def test_validate_schema_coerces_types():
    """Valid rows should have coerced types."""
    _setup()
    try:
        from pipeline import read_csv, validate_schema

        rows = read_csv(str(WORKSPACE / "example.csv"))
        schema = {"name": "str", "age": "int", "salary": "float"}
        valid, errors = validate_schema(rows, schema)
        assert len(errors) == 0
        assert len(valid) == 4
        assert isinstance(valid[0]["age"], int)
        assert isinstance(valid[0]["salary"], float)
        assert valid[0]["age"] == 30
    finally:
        _cleanup()


def test_transform_operations():
    """Transform operations work correctly."""
    _setup()
    try:
        from pipeline import transform

        rows = [
            {"name": "  Alice  ", "dept": "engineering", "salary": 75000.567},
            {"name": "  Bob  ", "dept": "MARKETING", "salary": -65000.123},
        ]
        transforms = [
            {"column": "name", "operation": "strip"},
            {"column": "dept", "operation": "upper"},
            {"column": "salary", "operation": "round", "decimals": 2},
        ]
        result = transform(rows, transforms)
        assert result[0]["name"] == "Alice"
        assert result[0]["dept"] == "ENGINEERING"
        assert result[0]["salary"] == 75000.57
        assert result[1]["salary"] == -65000.12
    finally:
        _cleanup()


def test_transform_abs():
    """abs transform on negative numbers."""
    _setup()
    try:
        from pipeline import read_csv, transform, validate_schema

        rows = read_csv(str(TEST_DATA / "negatives.csv"))
        schema = {"item": "str", "quantity": "int", "price": "float"}
        valid, _ = validate_schema(rows, schema)
        result = transform(
            valid,
            [
                {"column": "quantity", "operation": "abs"},
                {"column": "price", "operation": "abs"},
            ],
        )
        for row in result:
            assert row["quantity"] >= 0
            assert row["price"] >= 0.0
    finally:
        _cleanup()


def test_validate_output_constraints():
    """Output validation catches constraint violations."""
    _setup()
    try:
        from pipeline import validate_output

        rows = [
            {"name": "Alice", "age": 30, "dept": "Engineering"},
            {"name": "Bob", "age": 17, "dept": "Marketing"},
            {"name": "Alice", "age": 35, "dept": "Unknown"},
        ]
        constraints = [
            {"column": "name", "rule": "unique"},
            {"column": "age", "rule": "min", "value": 18},
            {"column": "dept", "rule": "in", "value": ["Engineering", "Marketing", "Sales"]},
        ]
        passed, errors = validate_output(rows, constraints)
        assert passed is False
        assert len(errors) >= 3  # duplicate name, under-age, unknown dept
    finally:
        _cleanup()


def test_write_csv_roundtrip():
    """Write and re-read should produce equivalent data."""
    _setup()
    try:
        from pipeline import read_csv, write_csv

        rows = [
            {"name": "Alice", "age": "30", "score": "95.5"},
            {"name": "Bob", "age": "25", "score": "87.3"},
        ]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            tmp_path = f.name

        write_csv(rows, tmp_path)
        reread = read_csv(tmp_path)
        assert len(reread) == 2
        assert reread[0]["name"] == "Alice"
        assert reread[1]["score"] == "87.3"

        Path(tmp_path).unlink(missing_ok=True)
    finally:
        _cleanup()


def test_write_csv_empty():
    """Writing empty rows should not crash."""
    _setup()
    try:
        from pipeline import write_csv

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            tmp_path = f.name

        write_csv([], tmp_path)
        assert Path(tmp_path).exists()
        Path(tmp_path).unlink(missing_ok=True)
    finally:
        _cleanup()

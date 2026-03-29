"""Validation utilities for DataProcessor instances and their data."""

from __future__ import annotations

from typing import Any

from processor import DataProcessor


def validate_processor(processor: DataProcessor) -> list[str]:
    """Validate that a DataProcessor is properly configured.

    Checks:
    - Has at least one step
    - Has a non-empty name
    - Step labels are unique

    Args:
        processor: The DataProcessor to validate.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []
    if not processor.name:
        errors.append("DataProcessor name must not be empty")
    if processor.step_count() == 0:
        errors.append("DataProcessor must have at least one step")
    labels = processor.step_labels()
    if len(labels) != len(set(labels)):
        errors.append("DataProcessor step labels must be unique")
    return errors


def validate_input_schema(
    data: list[dict[str, Any]],
    required_fields: list[str],
) -> list[str]:
    """Validate that input data conforms to expected schema.

    Each record must contain all required fields.

    Returns:
        List of validation error messages.
    """
    errors: list[str] = []
    for i, record in enumerate(data):
        for field in required_fields:
            if field not in record:
                errors.append(f"Record {i}: missing required field '{field}'")
    return errors


def validate_output(
    processor: DataProcessor,
    input_data: list[dict[str, Any]],
    expected_count: int | None = None,
) -> dict[str, Any]:
    """Run a DataProcessor and validate its output.

    Args:
        processor: The DataProcessor to test.
        input_data: Data to process.
        expected_count: Expected number of output records (None to skip check).

    Returns:
        Dict with 'valid' bool and 'errors' list.
    """
    errors: list[str] = []
    try:
        result = processor.run(input_data)
    except Exception as exc:
        return {"valid": False, "errors": [f"DataProcessor raised: {exc}"]}

    if expected_count is not None and len(result) != expected_count:
        errors.append(f"Expected {expected_count} records, got {len(result)}")

    return {"valid": len(errors) == 0, "errors": errors}

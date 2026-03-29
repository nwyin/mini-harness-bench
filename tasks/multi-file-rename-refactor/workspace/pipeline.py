"""Pipeline composition utilities for DataProcessor instances."""

from __future__ import annotations

from typing import Any, Callable

from processor import DataProcessor


def create_pipeline(name: str, steps: list[Callable], strict: bool = False) -> DataProcessor:
    """Create a DataProcessor with the given steps pre-registered.

    Args:
        name: Name for the DataProcessor instance.
        steps: List of callable steps to add.
        strict: Whether the DataProcessor should halt on errors.

    Returns:
        A configured DataProcessor ready to run.
    """
    proc = DataProcessor(name=name, strict=strict)
    for step in steps:
        proc.add_step(step)
    return proc


def chain_processors(*processors: DataProcessor) -> Callable[[list[dict[str, Any]]], list[dict[str, Any]]]:
    """Chain multiple DataProcessor instances into a single callable.

    Each DataProcessor's output feeds into the next one's input.
    """

    def chained(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        current = data
        for proc in processors:
            current = proc.run(current)
        return current

    return chained


def merge_histories(*processors: DataProcessor) -> list[dict[str, Any]]:
    """Merge execution histories from multiple DataProcessor instances."""
    combined: list[dict[str, Any]] = []
    for proc in processors:
        for entry in proc.get_history():
            combined.append({"processor": proc.name, **entry})
    return combined

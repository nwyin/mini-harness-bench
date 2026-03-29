"""Execution runner for DataProcessor pipelines."""

from __future__ import annotations

import time
from typing import Any

from processor import DataProcessor


class RunResult:
    """Holds the result of a DataProcessor execution."""

    def __init__(
        self,
        processor_name: str,
        input_count: int,
        output_count: int,
        elapsed_ms: float,
        history: list[dict[str, Any]],
    ) -> None:
        self.processor_name = processor_name
        self.input_count = input_count
        self.output_count = output_count
        self.elapsed_ms = elapsed_ms
        self.history = history

    def summary(self) -> dict[str, Any]:
        return {
            "processor": self.processor_name,
            "input_count": self.input_count,
            "output_count": self.output_count,
            "elapsed_ms": self.elapsed_ms,
            "steps_executed": len(self.history),
        }


def execute(processor: DataProcessor, data: list[dict[str, Any]]) -> RunResult:
    """Execute a DataProcessor and capture timing and results.

    Args:
        processor: The DataProcessor instance to run.
        data: Input data to process.

    Returns:
        RunResult with execution details.
    """
    processor.clear_history()
    start = time.monotonic()
    result = processor.run(data)
    elapsed = (time.monotonic() - start) * 1000
    return RunResult(
        processor_name=processor.name,
        input_count=len(data),
        output_count=len(result),
        elapsed_ms=elapsed,
        history=processor.get_history(),
    )


def execute_batch(
    processor: DataProcessor,
    batches: list[list[dict[str, Any]]],
) -> list[RunResult]:
    """Execute a DataProcessor on multiple batches of data.

    The DataProcessor history is cleared before each batch.
    """
    results = []
    for batch in batches:
        results.append(execute(processor, batch))
    return results

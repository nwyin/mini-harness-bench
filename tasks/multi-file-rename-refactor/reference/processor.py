"""Core data processing engine.

The PipelineExecutor class (formerly DataProcessor) is the central abstraction
for all data transformation work in this system.
"""

from __future__ import annotations

from typing import Any, Callable


class PipelineExecutor:
    """Processes data through a series of configurable steps.

    A PipelineExecutor instance holds a sequence of transformation steps and
    applies them in order to input data. Each step is a callable that takes
    a list of records and returns a transformed list.

    Example usage:
        executor = PipelineExecutor(name="etl")
        executor.add_step(normalize)
        executor.add_step(deduplicate)
        result = executor.run(raw_data)
    """

    def __init__(self, name: str, strict: bool = False) -> None:
        self.name = name
        self.strict = strict
        self._steps: list[tuple[str, Callable]] = []
        self._history: list[dict[str, Any]] = []

    def add_step(self, fn: Callable, label: str | None = None) -> None:
        """Add a processing step to the pipeline."""
        step_label = label or fn.__name__
        self._steps.append((step_label, fn))

    def run(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute all steps on the input data and return results.

        Each step receives the output of the previous step. If strict mode
        is enabled, any step that raises an exception will halt the pipeline.
        """
        current = list(data)
        for label, fn in self._steps:
            try:
                current = fn(current)
                self._history.append({"step": label, "status": "ok", "count": len(current)})
            except Exception as exc:
                self._history.append({"step": label, "status": "error", "error": str(exc)})
                if self.strict:
                    raise
        return current

    def get_history(self) -> list[dict[str, Any]]:
        """Return execution history for all runs."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear execution history."""
        self._history.clear()

    def step_count(self) -> int:
        """Return the number of registered steps."""
        return len(self._steps)

    def step_labels(self) -> list[str]:
        """Return labels of all registered steps."""
        return [label for label, _ in self._steps]

    def __repr__(self) -> str:
        return f"PipelineExecutor(name={self.name!r}, steps={self.step_count()})"

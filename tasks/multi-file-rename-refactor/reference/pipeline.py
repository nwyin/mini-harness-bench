"""Pipeline composition utilities for PipelineExecutor instances."""

from __future__ import annotations

from typing import Any, Callable

from processor import PipelineExecutor


def create_pipeline(name: str, steps: list[Callable], strict: bool = False) -> PipelineExecutor:
    """Create a PipelineExecutor with the given steps pre-registered.

    Args:
        name: Name for the PipelineExecutor instance.
        steps: List of callable steps to add.
        strict: Whether the PipelineExecutor should halt on errors.

    Returns:
        A configured PipelineExecutor ready to run.
    """
    proc = PipelineExecutor(name=name, strict=strict)
    for step in steps:
        proc.add_step(step)
    return proc


def chain_processors(*processors: PipelineExecutor) -> Callable[[list[dict[str, Any]]], list[dict[str, Any]]]:
    """Chain multiple PipelineExecutor instances into a single callable.

    Each PipelineExecutor's output feeds into the next one's input.
    """

    def chained(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        current = data
        for proc in processors:
            current = proc.run(current)
        return current

    return chained


def merge_histories(*processors: PipelineExecutor) -> list[dict[str, Any]]:
    """Merge execution histories from multiple PipelineExecutor instances."""
    combined: list[dict[str, Any]] = []
    for proc in processors:
        for entry in proc.get_history():
            combined.append({"processor": proc.name, **entry})
    return combined

"""Configuration and factory functions for PipelineExecutor creation."""

from __future__ import annotations

from typing import Any, Callable

from processor import PipelineExecutor


# Default step functions
def lowercase_keys(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lowercase all dictionary keys."""
    return [{k.lower(): v for k, v in row.items()} for row in data]


def remove_nulls(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove keys with None values."""
    return [{k: v for k, v in row.items() if v is not None} for row in data]


def add_row_index(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add a _row_index field to each record."""
    return [{**row, "_row_index": i} for i, row in enumerate(data)]


# Preset configurations for PipelineExecutor
PRESETS: dict[str, dict[str, Any]] = {
    "clean": {
        "steps": [lowercase_keys, remove_nulls],
        "strict": False,
    },
    "indexed": {
        "steps": [add_row_index],
        "strict": False,
    },
    "strict_clean": {
        "steps": [lowercase_keys, remove_nulls],
        "strict": True,
    },
}


def create_from_preset(preset_name: str) -> PipelineExecutor:
    """Create a PipelineExecutor from a named preset configuration.

    Available presets: clean, indexed, strict_clean.

    Returns:
        A PipelineExecutor configured according to the preset.

    Raises:
        KeyError: If the preset name is not recognized.
    """
    preset = PRESETS[preset_name]
    proc = PipelineExecutor(name=f"preset-{preset_name}", strict=preset.get("strict", False))
    for step in preset["steps"]:
        proc.add_step(step)
    return proc


def create_custom(
    name: str,
    steps: list[Callable],
    strict: bool = False,
) -> PipelineExecutor:
    """Create a custom PipelineExecutor with the given steps.

    This factory function creates and configures a PipelineExecutor instance.
    """
    proc = PipelineExecutor(name=name, strict=strict)
    for step in steps:
        proc.add_step(step)
    return proc

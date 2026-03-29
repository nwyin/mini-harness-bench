"""Global registry for named PipelineExecutor instances."""

from __future__ import annotations

from typing import Any

from processor import PipelineExecutor

_REGISTRY: dict[str, PipelineExecutor] = {}


def register_processor(processor: PipelineExecutor) -> None:
    """Register a PipelineExecutor by its name.

    If a PipelineExecutor with the same name already exists, it is overwritten.

    Args:
        processor: The PipelineExecutor instance to register.
    """
    _REGISTRY[processor.name] = processor


def get_processor(name: str) -> PipelineExecutor | None:
    """Retrieve a registered PipelineExecutor by name.

    Returns:
        The PipelineExecutor if found, None otherwise.
    """
    return _REGISTRY.get(name)


def list_processors() -> list[str]:
    """List all registered PipelineExecutor names."""
    return list(_REGISTRY.keys())


def unregister_processor(name: str) -> bool:
    """Remove a PipelineExecutor from the registry.

    Returns:
        True if the PipelineExecutor was found and removed, False otherwise.
    """
    if name in _REGISTRY:
        del _REGISTRY[name]
        return True
    return False


def clear_registry() -> None:
    """Remove all PipelineExecutor instances from the registry."""
    _REGISTRY.clear()


def get_registry_snapshot() -> dict[str, dict[str, Any]]:
    """Return a snapshot of all registered PipelineExecutor instances.

    Returns:
        Dict mapping names to PipelineExecutor metadata.
    """
    return {
        name: {
            "name": proc.name,
            "strict": proc.strict,
            "step_count": proc.step_count(),
            "step_labels": proc.step_labels(),
        }
        for name, proc in _REGISTRY.items()
    }

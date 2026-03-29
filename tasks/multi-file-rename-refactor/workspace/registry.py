"""Global registry for named DataProcessor instances."""

from __future__ import annotations

from typing import Any

from processor import DataProcessor

_REGISTRY: dict[str, DataProcessor] = {}


def register_processor(processor: DataProcessor) -> None:
    """Register a DataProcessor by its name.

    If a DataProcessor with the same name already exists, it is overwritten.

    Args:
        processor: The DataProcessor instance to register.
    """
    _REGISTRY[processor.name] = processor


def get_processor(name: str) -> DataProcessor | None:
    """Retrieve a registered DataProcessor by name.

    Returns:
        The DataProcessor if found, None otherwise.
    """
    return _REGISTRY.get(name)


def list_processors() -> list[str]:
    """List all registered DataProcessor names."""
    return list(_REGISTRY.keys())


def unregister_processor(name: str) -> bool:
    """Remove a DataProcessor from the registry.

    Returns:
        True if the DataProcessor was found and removed, False otherwise.
    """
    if name in _REGISTRY:
        del _REGISTRY[name]
        return True
    return False


def clear_registry() -> None:
    """Remove all DataProcessor instances from the registry."""
    _REGISTRY.clear()


def get_registry_snapshot() -> dict[str, dict[str, Any]]:
    """Return a snapshot of all registered DataProcessor instances.

    Returns:
        Dict mapping names to DataProcessor metadata.
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

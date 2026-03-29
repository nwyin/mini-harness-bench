"""Hook system for DataProcessor lifecycle events."""

from __future__ import annotations

from typing import Any, Callable

from processor import DataProcessor

HookFn = Callable[[DataProcessor, dict[str, Any]], None]


class HookRegistry:
    """Registry of lifecycle hooks for DataProcessor instances.

    Hooks are called at specific points during DataProcessor execution:
    - before_run: called before DataProcessor.run()
    - after_run: called after DataProcessor.run() completes
    - on_error: called when DataProcessor.run() raises an exception
    """

    def __init__(self) -> None:
        self._hooks: dict[str, list[HookFn]] = {
            "before_run": [],
            "after_run": [],
            "on_error": [],
        }

    def register(self, event: str, hook: HookFn) -> None:
        """Register a hook for a lifecycle event.

        Args:
            event: One of 'before_run', 'after_run', 'on_error'.
            hook: Callable that receives the DataProcessor and context dict.
        """
        if event not in self._hooks:
            raise ValueError(f"Unknown event: {event}. Must be one of {list(self._hooks)}")
        self._hooks[event].append(hook)

    def trigger(self, event: str, processor: DataProcessor, context: dict[str, Any]) -> None:
        """Trigger all hooks for an event.

        Args:
            event: The lifecycle event name.
            processor: The DataProcessor instance.
            context: Additional context data.
        """
        for hook in self._hooks.get(event, []):
            hook(processor, context)

    def clear(self, event: str | None = None) -> None:
        """Clear hooks for a specific event, or all hooks if event is None."""
        if event is None:
            for key in self._hooks:
                self._hooks[key].clear()
        elif event in self._hooks:
            self._hooks[event].clear()


def run_with_hooks(
    processor: DataProcessor,
    data: list[dict[str, Any]],
    registry: HookRegistry,
) -> list[dict[str, Any]]:
    """Execute a DataProcessor with lifecycle hooks.

    This wraps DataProcessor.run() with before/after/error hooks from the registry.
    """
    context: dict[str, Any] = {"input_count": len(data)}
    registry.trigger("before_run", processor, context)
    try:
        result = processor.run(data)
        context["output_count"] = len(result)
        registry.trigger("after_run", processor, context)
        return result
    except Exception as exc:
        context["error"] = str(exc)
        registry.trigger("on_error", processor, context)
        raise

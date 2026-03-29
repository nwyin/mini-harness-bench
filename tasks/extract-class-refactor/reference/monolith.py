"""AppManager: handles configuration, logging, and metrics for the application."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from metrics import MetricsCollector


class ConfigError(Exception):
    """Raised when a configuration value is invalid."""


class AppManager:
    """Manages config, logging, and delegates metrics to MetricsCollector."""

    # ------------------------------------------------------------------ #
    #  Initialisation
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        app_name: str,
        config_path: str | Path | None = None,
        log_level: str = "INFO",
        metrics_namespace: str = "default",
    ) -> None:
        self.app_name = app_name
        self.log_level = log_level
        self.metrics_namespace = metrics_namespace

        # Config state
        self._config: dict[str, Any] = {}
        self._config_path = Path(config_path) if config_path else None
        self._config_loaded = False

        # Logging state
        self._log_buffer: list[dict[str, Any]] = []
        self._log_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        self._min_log_level = self._log_levels.index(log_level)

        # Metrics delegation
        self._metrics_collector = MetricsCollector(namespace=metrics_namespace)

    # ------------------------------------------------------------------ #
    #  Configuration methods
    # ------------------------------------------------------------------ #

    def load_config(self, overrides: dict[str, Any] | None = None) -> None:
        """Load configuration from file and apply overrides."""
        if self._config_path and self._config_path.exists():
            with open(self._config_path) as f:
                self._config = json.load(f)
        else:
            self._config = {}
        if overrides:
            self._config.update(overrides)
        self._config_loaded = True

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        if not self._config_loaded:
            self.load_config()
        return self._config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        if not self._config_loaded:
            self.load_config()
        self._config[key] = value

    def validate_config(self, required_keys: list[str]) -> list[str]:
        """Validate that all required keys are present. Return missing keys."""
        if not self._config_loaded:
            self.load_config()
        return [k for k in required_keys if k not in self._config]

    def save_config(self, path: str | Path | None = None) -> None:
        """Save current configuration to a JSON file."""
        target = Path(path) if path else self._config_path
        if target is None:
            raise ConfigError("No config path specified")
        with open(target, "w") as f:
            json.dump(self._config, f, indent=2)

    def get_all_config(self) -> dict[str, Any]:
        """Return a copy of the full configuration."""
        if not self._config_loaded:
            self.load_config()
        return dict(self._config)

    def merge_config(self, other: dict[str, Any]) -> None:
        """Merge another config dict, with other taking priority."""
        if not self._config_loaded:
            self.load_config()
        self._config.update(other)

    # ------------------------------------------------------------------ #
    #  Logging methods
    # ------------------------------------------------------------------ #

    def log(self, level: str, message: str, **context: Any) -> None:
        """Write a structured log entry."""
        level = level.upper()
        if level not in self._log_levels:
            level = "INFO"
        level_idx = self._log_levels.index(level)
        if level_idx < self._min_log_level:
            return
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "app": self.app_name,
            "message": message,
            **context,
        }
        self._log_buffer.append(entry)

    def debug(self, message: str, **context: Any) -> None:
        self.log("DEBUG", message, **context)

    def info(self, message: str, **context: Any) -> None:
        self.log("INFO", message, **context)

    def warning(self, message: str, **context: Any) -> None:
        self.log("WARNING", message, **context)

    def error(self, message: str, **context: Any) -> None:
        self.log("ERROR", message, **context)

    def critical(self, message: str, **context: Any) -> None:
        self.log("CRITICAL", message, **context)

    def get_logs(self, level: str | None = None) -> list[dict[str, Any]]:
        """Return log entries, optionally filtered by level."""
        if level is None:
            return list(self._log_buffer)
        return [e for e in self._log_buffer if e["level"] == level.upper()]

    def clear_logs(self) -> None:
        """Clear the log buffer."""
        self._log_buffer.clear()

    def export_logs(self, path: str | Path) -> int:
        """Export logs to a JSONL file. Return the number of entries written."""
        p = Path(path)
        count = 0
        with open(p, "w") as f:
            for entry in self._log_buffer:
                f.write(json.dumps(entry) + "\n")
                count += 1
        return count

    def set_log_level(self, level: str) -> None:
        """Change the minimum log level."""
        level = level.upper()
        if level in self._log_levels:
            self._min_log_level = self._log_levels.index(level)
            self.log_level = level

    def format_log_entry(self, entry: dict[str, Any]) -> str:
        """Format a log entry as a human-readable string."""
        ts = entry.get("timestamp", "?")
        lvl = entry.get("level", "?")
        msg = entry.get("message", "")
        extra = {k: v for k, v in entry.items() if k not in ("timestamp", "level", "app", "message")}
        base = f"[{ts}] {lvl}: {msg}"
        if extra:
            base += f" | {json.dumps(extra)}"
        return base

    # ------------------------------------------------------------------ #
    #  Metrics methods — delegated to MetricsCollector
    # ------------------------------------------------------------------ #

    def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        self._metrics_collector.record_metric(name, value, tags)

    def get_metric(self, name: str) -> list[float]:
        return self._metrics_collector.get_metric(name)

    def get_all_metrics(self) -> dict[str, list[float]]:
        return self._metrics_collector.get_all_metrics()

    def aggregate_metrics(self, name: str) -> dict[str, float]:
        return self._metrics_collector.aggregate_metrics(name)

    def reset_metrics(self) -> None:
        self._metrics_collector.reset_metrics()

    def export_metrics_report(self) -> dict[str, Any]:
        return self._metrics_collector.export_metrics_report()

    # ------------------------------------------------------------------ #
    #  Lifecycle helpers
    # ------------------------------------------------------------------ #

    def status(self) -> dict[str, Any]:
        """Return a status snapshot of the manager."""
        return {
            "app_name": self.app_name,
            "config_loaded": self._config_loaded,
            "config_keys": len(self._config),
            "log_level": self.log_level,
            "log_entries": len(self._log_buffer),
            "metrics_namespace": self.metrics_namespace,
            "metrics_count": sum(len(v) for v in self._metrics_collector.get_all_metrics().values()),
            "uptime_seconds": time.monotonic() - self._metrics_collector._metrics_start_time,
        }

    def reset_all(self) -> None:
        """Reset all internal state."""
        self._config.clear()
        self._config_loaded = False
        self.clear_logs()
        self.reset_metrics()

    # ------------------------------------------------------------------ #
    #  Convenience: combined operations
    # ------------------------------------------------------------------ #

    def record_and_log(self, metric_name: str, value: float, log_level: str = "DEBUG") -> None:
        """Record a metric and also emit a log entry about it."""
        self.record_metric(metric_name, value)
        self.log(log_level, f"Metric {metric_name}={value}")

    def health_check(self) -> dict[str, Any]:
        """Run a basic health check and return results."""
        issues: list[str] = []
        if not self._config_loaded:
            issues.append("config_not_loaded")
        if len(self._log_buffer) > 10000:
            issues.append("log_buffer_large")
        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "status": self.status(),
        }

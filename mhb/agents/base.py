from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False
    wall_time_sec: float = 0.0
    tokens: dict | None = None
    cost_usd: float | None = None
    trajectory_events: list[dict] = field(default_factory=list)

    def merge(self, other: AgentResult) -> AgentResult:
        """Merge another result into this one, accumulating tokens and events."""
        merged_tokens = None
        if self.tokens or other.tokens:
            merged_tokens = {}
            for key in ("input", "output", "cache_read", "cache_write"):
                merged_tokens[key] = (self.tokens or {}).get(key, 0) + (other.tokens or {}).get(key, 0)

        return AgentResult(
            stdout=self.stdout + other.stdout,
            stderr=self.stderr + other.stderr,
            exit_code=other.exit_code,
            timed_out=other.timed_out,
            wall_time_sec=self.wall_time_sec + other.wall_time_sec,
            tokens=merged_tokens,
            cost_usd=(self.cost_usd or 0) + (other.cost_usd or 0),
            trajectory_events=self.trajectory_events + other.trajectory_events,
        )


class BaseAgent(ABC):
    name: str

    @abstractmethod
    def run(self, instruction: str, workdir: Path, timeout: int, model: str | None = None, task_id: str | None = None) -> AgentResult: ...

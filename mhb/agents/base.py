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


class BaseAgent(ABC):
    name: str

    @abstractmethod
    def run(self, instruction: str, workdir: Path, timeout: int, model: str | None = None, task_id: str | None = None) -> AgentResult: ...

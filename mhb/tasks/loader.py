from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

TIER_ORDER = {"smoke": 0, "standard": 1, "full": 2}


@dataclass
class Task:
    task_id: str
    instruction: str
    category: str
    difficulty: str
    tier: str
    tags: list[str] = field(default_factory=list)
    max_agent_time_sec: int | None = None
    expert_time_estimate_min: int | None = None
    task_dir: Path = field(default_factory=lambda: Path("."))

    @property
    def workspace_dir(self) -> Path:
        return self.task_dir / "workspace"

    @property
    def tests_dir(self) -> Path:
        return self.task_dir / "tests"

    @property
    def reference_dir(self) -> Path:
        return self.task_dir / "reference"

    @property
    def setup_script(self) -> Path | None:
        p = self.task_dir / "setup.sh"
        return p if p.exists() else None


def load_task(task_dir: Path) -> Task:
    yaml_path = task_dir / "task.yaml"
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return Task(
        task_id=task_dir.name,
        instruction=data["instruction"],
        category=data["category"],
        difficulty=data["difficulty"],
        tier=data["tier"],
        tags=data.get("tags", []),
        max_agent_time_sec=data.get("max_agent_time_sec"),
        expert_time_estimate_min=data.get("expert_time_estimate_min"),
        task_dir=task_dir,
    )


def discover_tasks(tasks_root: Path | None = None) -> list[Task]:
    if tasks_root is None:
        tasks_root = Path(os.environ.get("MHB_TASKS_DIR", Path(__file__).parent.parent.parent / "tasks"))
    tasks = []
    if not tasks_root.exists():
        return tasks
    for d in sorted(tasks_root.iterdir()):
        if d.is_dir() and (d / "task.yaml").exists():
            tasks.append(load_task(d))
    return tasks


def filter_by_tier(tasks: list[Task], tier: str) -> list[Task]:
    max_tier = TIER_ORDER.get(tier, 2)
    return [t for t in tasks if TIER_ORDER.get(t.tier, 2) <= max_tier]

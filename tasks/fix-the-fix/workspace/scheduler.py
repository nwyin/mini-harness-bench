"""Task scheduler with timezone-aware scheduling.

Supports both one-shot (absolute) and recurring (relative) schedules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from zoneinfo import ZoneInfo


class ScheduleType(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class ScheduledTask:
    task_id: str
    name: str
    schedule_type: ScheduleType
    scheduled_time: datetime  # The time this task should fire
    tz: ZoneInfo  # The timezone the user specified
    weekday: int | None = None  # 0=Monday, 6=Sunday (for weekly)
    enabled: bool = True
    last_run: datetime | None = None
    metadata: dict = field(default_factory=dict)


class Scheduler:
    """Timezone-aware task scheduler."""

    def __init__(self):
        self._tasks: dict[str, ScheduledTask] = {}

    def schedule_task(
        self,
        task_id: str,
        name: str,
        schedule_type: str,
        hour: int,
        minute: int,
        tz_name: str = "UTC",
        weekday: int | None = None,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
        metadata: dict | None = None,
    ) -> ScheduledTask:
        """Schedule a new task.

        For ONCE: year, month, day, hour, minute in the given timezone.
        For DAILY: hour, minute in the given timezone, repeats every day.
        For WEEKLY: hour, minute, weekday in the given timezone, repeats weekly.
        """
        stype = ScheduleType(schedule_type)
        tz = ZoneInfo(tz_name)

        if stype == ScheduleType.ONCE:
            if not all([year, month, day]):
                raise ValueError("ONCE schedule requires year, month, day")
            local_dt = datetime(year, month, day, hour, minute, tzinfo=tz)
            # Convert to UTC for storage
            scheduled_time = local_dt.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
        elif stype == ScheduleType.DAILY:
            # Store the time in UTC directly
            now_utc = datetime.now(timezone.utc)
            scheduled_time = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=timezone.utc)
            if scheduled_time <= now_utc:
                scheduled_time += timedelta(days=1)
        elif stype == ScheduleType.WEEKLY:
            if weekday is None:
                raise ValueError("WEEKLY schedule requires weekday")
            now_utc = datetime.now(timezone.utc)
            scheduled_time = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=timezone.utc)
            # Advance to the correct weekday
            days_ahead = weekday - scheduled_time.weekday()
            if days_ahead < 0:
                days_ahead += 7
            if days_ahead == 0 and scheduled_time <= now_utc:
                days_ahead = 7
            scheduled_time += timedelta(days=days_ahead)
        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=stype,
            scheduled_time=scheduled_time,
            tz=tz,
            weekday=weekday,
            enabled=True,
            metadata=metadata or {},
        )
        self._tasks[task_id] = task
        return task

    def get_next_occurrence(self, task_id: str, after: datetime | None = None) -> datetime:
        """Get the next occurrence of a scheduled task.

        For ONCE: returns the scheduled time (in UTC).
        For DAILY: returns the next daily occurrence (in UTC).
        For WEEKLY: returns the next weekly occurrence (in UTC).

        The returned datetime is always in UTC.
        """
        task = self._tasks[task_id]
        if after is None:
            after = datetime.now(timezone.utc)
        elif after.tzinfo is None:
            after = after.replace(tzinfo=timezone.utc)
        else:
            after = after.astimezone(timezone.utc)

        if task.schedule_type == ScheduleType.ONCE:
            return task.scheduled_time

        if task.schedule_type == ScheduleType.DAILY:
            # Next occurrence at the scheduled hour:minute UTC
            candidate = after.replace(
                hour=task.scheduled_time.hour,
                minute=task.scheduled_time.minute,
                second=0,
                microsecond=0,
            )
            if candidate <= after:
                candidate += timedelta(days=1)
            return candidate

        if task.schedule_type == ScheduleType.WEEKLY:
            candidate = after.replace(
                hour=task.scheduled_time.hour,
                minute=task.scheduled_time.minute,
                second=0,
                microsecond=0,
            )
            days_ahead = task.weekday - candidate.weekday()
            if days_ahead < 0:
                days_ahead += 7
            candidate += timedelta(days=days_ahead)
            if candidate <= after:
                candidate += timedelta(weeks=1)
            return candidate

        raise ValueError(f"Unknown schedule type: {task.schedule_type}")

    def get_next_occurrence_local(self, task_id: str, after: datetime | None = None) -> datetime:
        """Get the next occurrence in the task's local timezone."""
        utc_time = self.get_next_occurrence(task_id, after)
        task = self._tasks[task_id]
        return utc_time.astimezone(task.tz)

    def get_pending_tasks(self, now: datetime | None = None) -> list[ScheduledTask]:
        """Get all tasks that should fire at or before the given time."""
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        else:
            now = now.astimezone(timezone.utc)

        pending = []
        for task in self._tasks.values():
            if not task.enabled:
                continue
            next_time = self.get_next_occurrence(task.task_id, after=task.last_run or datetime.min.replace(tzinfo=timezone.utc))
            if next_time <= now:
                pending.append(task)
        return pending

    def mark_run(self, task_id: str, run_time: datetime | None = None) -> None:
        """Mark a task as having been run."""
        task = self._tasks[task_id]
        if run_time is None:
            run_time = datetime.now(timezone.utc)
        task.last_run = run_time

    def get_task(self, task_id: str) -> ScheduledTask:
        """Get a task by ID."""
        return self._tasks[task_id]

    def list_tasks(self) -> list[ScheduledTask]:
        """List all tasks."""
        return list(self._tasks.values())

    def remove_task(self, task_id: str) -> None:
        """Remove a task."""
        del self._tasks[task_id]

    def disable_task(self, task_id: str) -> None:
        """Disable a task (won't fire until re-enabled)."""
        self._tasks[task_id].enabled = False

    def enable_task(self, task_id: str) -> None:
        """Enable a disabled task."""
        self._tasks[task_id].enabled = True

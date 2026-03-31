#!/bin/bash
set -e

git config user.email "dev@example.com"
git config user.name "Developer"

# Reset to empty state
git rm -rf . --quiet
git commit -m "remove initial" --allow-empty --quiet

# Write BUGFIX.md (same across all commits after commit 2)
write_bugfix() {
cat > BUGFIX.md << 'MDEOF'
# Bug Report: Timezone Handling in Scheduler

## Original Bug (Fixed)

**Reported:** Tasks scheduled in non-UTC timezones fire at wrong times.

**Root cause:** In `_apply_timezone_offset`, the offset was being added instead
of subtracted when converting local time to UTC. For example, a task at 9am
US/Eastern (UTC-5) was being stored as 4am UTC instead of 2pm UTC.

**Fix applied:** The developer force-converted all schedule times to UTC in
`schedule_task()` by replacing the timezone with UTC. This fixed the immediate
issue of wrong fire times for absolute schedules.

## New Issue (Needs Fix)

After the fix, relative/recurring schedules are broken. A task configured as
"every day at 09:00" in the US/Eastern timezone now fires at 09:00 UTC instead
of 09:00 Eastern.

The `get_next_occurrence()` method needs to return times that respect the
original local timezone for recurring schedules, while still correctly
handling the UTC conversion for absolute (one-shot) schedules.

## Expected Behavior

- **Absolute schedule** (one-shot, specific datetime): Convert to UTC correctly
  for internal storage, fire at the right wall-clock moment.
- **Relative/recurring schedule** (daily/weekly at a given local time): The
  recurrence should be computed in the task's local timezone. "Every day at
  9am Eastern" means 9am Eastern every day, which is 14:00 UTC in winter and
  13:00 UTC in summer.
MDEOF
}

# --- Commit 1: Original code with timezone bug ---
cat > scheduler.py << 'PYEOF'
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
    scheduled_time: datetime
    tz: ZoneInfo
    weekday: int | None = None
    enabled: bool = True
    last_run: datetime | None = None
    metadata: dict = field(default_factory=dict)


class Scheduler:
    """Timezone-aware task scheduler."""

    def __init__(self):
        self._tasks: dict[str, ScheduledTask] = {}

    def _apply_timezone_offset(self, local_dt: datetime, tz: ZoneInfo) -> datetime:
        """Convert a local datetime to UTC.

        BUG: adds offset instead of subtracting it.
        """
        offset = local_dt.replace(tzinfo=tz).utcoffset()
        # BUG: should subtract offset, but adds it
        utc_dt = local_dt.replace(tzinfo=timezone.utc) + offset
        return utc_dt

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
        stype = ScheduleType(schedule_type)
        tz = ZoneInfo(tz_name)

        if stype == ScheduleType.ONCE:
            if not all([year, month, day]):
                raise ValueError("ONCE schedule requires year, month, day")
            local_dt = datetime(year, month, day, hour, minute)
            scheduled_time = self._apply_timezone_offset(local_dt, tz)
        elif stype == ScheduleType.DAILY:
            now_local = datetime.now(tz)
            scheduled_time_local = now_local.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            if scheduled_time_local <= now_local:
                scheduled_time_local += timedelta(days=1)
            scheduled_time = self._apply_timezone_offset(
                scheduled_time_local.replace(tzinfo=None), tz
            )
        elif stype == ScheduleType.WEEKLY:
            if weekday is None:
                raise ValueError("WEEKLY schedule requires weekday")
            now_local = datetime.now(tz)
            scheduled_time_local = now_local.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            days_ahead = weekday - scheduled_time_local.weekday()
            if days_ahead < 0:
                days_ahead += 7
            if days_ahead == 0 and scheduled_time_local <= now_local:
                days_ahead = 7
            scheduled_time_local += timedelta(days=days_ahead)
            scheduled_time = self._apply_timezone_offset(
                scheduled_time_local.replace(tzinfo=None), tz
            )
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
            after_local = after.astimezone(task.tz)
            candidate = after_local.replace(
                hour=task.scheduled_time.hour,
                minute=task.scheduled_time.minute,
                second=0,
                microsecond=0,
            )
            if candidate <= after_local:
                candidate += timedelta(days=1)
            return candidate.astimezone(timezone.utc)

        if task.schedule_type == ScheduleType.WEEKLY:
            after_local = after.astimezone(task.tz)
            candidate = after_local.replace(
                hour=task.scheduled_time.hour,
                minute=task.scheduled_time.minute,
                second=0,
                microsecond=0,
            )
            days_ahead = task.weekday - candidate.weekday()
            if days_ahead < 0:
                days_ahead += 7
            candidate += timedelta(days=days_ahead)
            if candidate <= after_local:
                candidate += timedelta(weeks=1)
            return candidate.astimezone(timezone.utc)

        raise ValueError(f"Unknown schedule type: {task.schedule_type}")

    def get_next_occurrence_local(self, task_id: str, after: datetime | None = None) -> datetime:
        utc_time = self.get_next_occurrence(task_id, after)
        task = self._tasks[task_id]
        return utc_time.astimezone(task.tz)

    def get_pending_tasks(self, now: datetime | None = None) -> list[ScheduledTask]:
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
        task = self._tasks[task_id]
        if run_time is None:
            run_time = datetime.now(timezone.utc)
        task.last_run = run_time

    def get_task(self, task_id: str) -> ScheduledTask:
        return self._tasks[task_id]

    def list_tasks(self) -> list[ScheduledTask]:
        return list(self._tasks.values())

    def remove_task(self, task_id: str) -> None:
        del self._tasks[task_id]

    def disable_task(self, task_id: str) -> None:
        self._tasks[task_id].enabled = False

    def enable_task(self, task_id: str) -> None:
        self._tasks[task_id].enabled = True
PYEOF

git add -A
git commit -m "Initial task scheduler with timezone support" --quiet

# --- Commit 2: Attempted timezone fix ---
cat > scheduler.py << 'PYEOF'
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
            scheduled_time = now_utc.replace(
                hour=hour, minute=minute, second=0, microsecond=0, tzinfo=timezone.utc
            )
            if scheduled_time <= now_utc:
                scheduled_time += timedelta(days=1)
        elif stype == ScheduleType.WEEKLY:
            if weekday is None:
                raise ValueError("WEEKLY schedule requires weekday")
            now_utc = datetime.now(timezone.utc)
            scheduled_time = now_utc.replace(
                hour=hour, minute=minute, second=0, microsecond=0, tzinfo=timezone.utc
            )
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
        utc_time = self.get_next_occurrence(task_id, after)
        task = self._tasks[task_id]
        return utc_time.astimezone(task.tz)

    def get_pending_tasks(self, now: datetime | None = None) -> list[ScheduledTask]:
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
        task = self._tasks[task_id]
        if run_time is None:
            run_time = datetime.now(timezone.utc)
        task.last_run = run_time

    def get_task(self, task_id: str) -> ScheduledTask:
        return self._tasks[task_id]

    def list_tasks(self) -> list[ScheduledTask]:
        return list(self._tasks.values())

    def remove_task(self, task_id: str) -> None:
        del self._tasks[task_id]

    def disable_task(self, task_id: str) -> None:
        self._tasks[task_id].enabled = False

    def enable_task(self, task_id: str) -> None:
        self._tasks[task_id].enabled = True
PYEOF

write_bugfix
git add -A
git commit -m "Fix timezone handling — convert all times to UTC

The original _apply_timezone_offset was adding the offset instead of
subtracting it, causing tasks in non-UTC timezones to fire at wrong
times. Simplified by converting everything to UTC directly.

Removed the buggy _apply_timezone_offset method entirely." --quiet

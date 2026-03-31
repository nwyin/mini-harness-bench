"""Tests for fix-the-fix task — scheduler timezone handling."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def _workspace():
    pp = os.environ.get("PYTHONPATH")
    if pp:
        return Path(pp)
    return Path(__file__).resolve().parent.parent / "workspace"


def _setup():
    ws = str(_workspace())
    if ws not in sys.path:
        sys.path.insert(0, ws)


def _cleanup():
    for mod_name in list(sys.modules):
        if mod_name in ("scheduler",):
            del sys.modules[mod_name]


def test_utc_scheduling():
    """UTC tasks should fire at the correct UTC time."""
    _setup()
    try:
        from scheduler import Scheduler

        s = Scheduler()
        s.schedule_task(
            "t1",
            "UTC task",
            "once",
            hour=14,
            minute=30,
            tz_name="UTC",
            year=2026,
            month=6,
            day=15,
        )
        nxt = s.get_next_occurrence("t1")
        assert nxt.hour == 14
        assert nxt.minute == 30
        assert nxt.tzinfo is not None
        # Should be UTC
        assert nxt.utcoffset() == timedelta(0)
    finally:
        _cleanup()


def test_nonlocal_absolute():
    """A one-shot task in US/Eastern at 9am should fire at 13:00 UTC (EDT) or 14:00 UTC (EST)."""
    _setup()
    try:
        from scheduler import Scheduler

        s = Scheduler()
        # June 15 2026 — EDT (UTC-4)
        s.schedule_task(
            "t2",
            "Eastern task",
            "once",
            hour=9,
            minute=0,
            tz_name="US/Eastern",
            year=2026,
            month=6,
            day=15,
        )
        nxt = s.get_next_occurrence("t2")
        # 9am EDT = 13:00 UTC
        utc_time = nxt.astimezone(timezone.utc)
        assert utc_time.hour == 13, f"Expected 13:00 UTC, got {utc_time.hour}:{utc_time.minute}"
        assert utc_time.minute == 0

        # January 15 2026 — EST (UTC-5)
        s.schedule_task(
            "t2b",
            "Eastern task winter",
            "once",
            hour=9,
            minute=0,
            tz_name="US/Eastern",
            year=2026,
            month=1,
            day=15,
        )
        nxt2 = s.get_next_occurrence("t2b")
        utc_time2 = nxt2.astimezone(timezone.utc)
        assert utc_time2.hour == 14, f"Expected 14:00 UTC, got {utc_time2.hour}:{utc_time2.minute}"
        assert utc_time2.minute == 0
    finally:
        _cleanup()


def test_relative_daily():
    """A daily task at 9am US/Eastern should recur at 9am Eastern, not 9am UTC."""
    _setup()
    try:
        from scheduler import Scheduler

        s = Scheduler()
        s.schedule_task("t3", "Daily Eastern", "daily", hour=9, minute=0, tz_name="US/Eastern")

        # Query for next occurrence after a specific UTC time
        # 2026-06-15 12:00 UTC = 8:00 AM EDT — so next 9am EDT = 13:00 UTC same day
        after = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        nxt = s.get_next_occurrence("t3", after=after)
        utc_time = nxt.astimezone(timezone.utc)
        assert utc_time.hour == 13, f"Expected 13:00 UTC (9am EDT), got {utc_time.hour}:{utc_time.minute}"
        assert utc_time.minute == 0
        assert utc_time.day == 15  # Same day, since 8am < 9am

        # After 9am EDT (13:00 UTC), next occurrence should be next day
        after2 = datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)  # 10am EDT
        nxt2 = s.get_next_occurrence("t3", after=after2)
        utc_time2 = nxt2.astimezone(timezone.utc)
        assert utc_time2.day == 16, f"Expected day 16, got {utc_time2.day}"
        assert utc_time2.hour == 13
    finally:
        _cleanup()


def test_relative_weekly():
    """A weekly task on Monday at 9am US/Eastern should respect local timezone."""
    _setup()
    try:
        from scheduler import Scheduler

        s = Scheduler()
        # Monday = 0
        s.schedule_task("t4", "Weekly Monday", "weekly", hour=9, minute=0, tz_name="US/Eastern", weekday=0)

        # 2026-06-15 is a Monday. Query after 8am EDT = 12:00 UTC
        after = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        nxt = s.get_next_occurrence("t4", after=after)
        utc_time = nxt.astimezone(timezone.utc)
        # 9am EDT = 13:00 UTC on Monday June 15
        assert utc_time.hour == 13, f"Expected 13:00 UTC, got {utc_time.hour}:{utc_time.minute}"
        assert utc_time.weekday() == 0  # Monday

        # After 9am EDT on Monday, next is next Monday
        after2 = datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)
        nxt2 = s.get_next_occurrence("t4", after=after2)
        utc_time2 = nxt2.astimezone(timezone.utc)
        assert utc_time2.weekday() == 0
        assert utc_time2.day == 22  # Next Monday
        assert utc_time2.hour == 13
    finally:
        _cleanup()


def test_dst_transition():
    """Daily task should handle DST transitions correctly.

    US/Eastern: EDT (UTC-4) in summer, EST (UTC-5) in winter.
    Spring forward 2026: March 8. Fall back 2026: November 1.
    """
    _setup()
    try:
        from scheduler import Scheduler

        s = Scheduler()
        s.schedule_task("t5", "Daily DST", "daily", hour=9, minute=0, tz_name="US/Eastern")

        # Day before spring forward: March 7, 2026 (EST, UTC-5)
        # 9am EST = 14:00 UTC
        after_winter = datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc)
        nxt_winter = s.get_next_occurrence("t5", after=after_winter)
        utc_winter = nxt_winter.astimezone(timezone.utc)
        assert utc_winter.hour == 14, f"Expected 14:00 UTC (9am EST), got {utc_winter.hour}"
        assert utc_winter.day == 7

        # Day after spring forward: March 9, 2026 (EDT, UTC-4)
        # 9am EDT = 13:00 UTC
        after_summer = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
        nxt_summer = s.get_next_occurrence("t5", after=after_summer)
        utc_summer = nxt_summer.astimezone(timezone.utc)
        assert utc_summer.hour == 13, f"Expected 13:00 UTC (9am EDT), got {utc_summer.hour}"
        assert utc_summer.day == 9

        # The local time should always be 9am regardless of DST
        local_winter = nxt_winter.astimezone(ZoneInfo("US/Eastern"))
        local_summer = nxt_summer.astimezone(ZoneInfo("US/Eastern"))
        assert local_winter.hour == 9, f"Expected local 9am, got {local_winter.hour}"
        assert local_summer.hour == 9, f"Expected local 9am, got {local_summer.hour}"
    finally:
        _cleanup()


def test_original_bug_fixed():
    """The original timezone offset bug must be fixed: non-UTC absolute times convert correctly.

    This is the same as test_nonlocal_absolute but more explicit about the original bug.
    """
    _setup()
    try:
        from scheduler import Scheduler

        s = Scheduler()
        # Tokyo (UTC+9): 9am JST = 0:00 UTC
        s.schedule_task(
            "t6",
            "Tokyo task",
            "once",
            hour=9,
            minute=0,
            tz_name="Asia/Tokyo",
            year=2026,
            month=6,
            day=15,
        )
        nxt = s.get_next_occurrence("t6")
        utc_time = nxt.astimezone(timezone.utc)
        assert utc_time.hour == 0, f"Expected 0:00 UTC (9am JST), got {utc_time.hour}:{utc_time.minute}"
        assert utc_time.day == 15

        # Original bug would have added +9 instead of subtracting:
        # 9am + 9h = 6pm UTC (wrong). Correct is 9am - 9h = 0:00 UTC.
        assert utc_time.hour != 18, "Original timezone bug still present (offset added instead of subtracted)"
    finally:
        _cleanup()

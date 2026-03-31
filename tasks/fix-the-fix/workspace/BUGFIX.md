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

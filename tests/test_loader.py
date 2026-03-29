from mhb.tasks.loader import discover_tasks, filter_by_tier


def test_discover_finds_tasks():
    tasks = discover_tasks()
    assert len(tasks) >= 5
    ids = {t.task_id for t in tasks}
    assert "implement-from-tests" in ids
    assert "fix-off-by-one" in ids
    assert "fix-git" in ids
    assert "pandas-etl" in ids
    assert "heterogeneous-dates" in ids


def test_task_fields():
    tasks = discover_tasks()
    t = next(t for t in tasks if t.task_id == "implement-from-tests")
    assert t.category == "software-engineering"
    assert t.difficulty == "easy"
    assert t.tier == "smoke"
    assert t.instruction.strip() != ""


def test_filter_smoke():
    tasks = discover_tasks()
    smoke = filter_by_tier(tasks, "smoke")
    assert all(t.tier == "smoke" for t in smoke)
    assert len(smoke) >= 5


def test_filter_standard_includes_smoke():
    tasks = discover_tasks()
    standard = filter_by_tier(tasks, "standard")
    smoke = filter_by_tier(tasks, "smoke")
    smoke_ids = {t.task_id for t in smoke}
    standard_ids = {t.task_id for t in standard}
    assert smoke_ids.issubset(standard_ids)


def test_filter_full_includes_all():
    tasks = discover_tasks()
    full = filter_by_tier(tasks, "full")
    assert len(full) == len(tasks)

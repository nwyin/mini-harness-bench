from __future__ import annotations


def _fmt_tokens(n: int) -> str:
    """Format token count compactly: 1,234 or 1.2M or 523K."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n // 1000}K"
    return f"{n:,}"


def format_results_table(results: dict) -> str:
    tasks = results.get("tasks", {})
    if not tasks:
        return "No task results."

    header = f"{'Task ID':<25} {'Score':>6} {'In+Out':>7} {'Cache':>7} {'Cost':>8} {'Time':>7} {'Status':<8}"
    sep = "-" * len(header)
    lines = [header, sep]

    for task_id, data in sorted(tasks.items()):
        correctness = data.get("correctness", 0.0)
        t = data.get("tokens") or {}
        in_out = t.get("input", 0) + t.get("output", 0)
        cache = t.get("cache_read", 0) + t.get("cache_write", 0)
        cost = data.get("cost_usd", 0.0) or 0.0
        wall = data.get("wall_time_sec", {}).get("total", 0.0)
        timed_out = data.get("timed_out", False)

        if correctness >= 1.0:
            status = "passed"
        elif timed_out and correctness == 0.0:
            status = "timeout"
        elif timed_out:
            status = "timeout*"
        elif correctness > 0.0:
            status = "partial"
        else:
            status = "failed"

        lines.append(
            f"{task_id:<25} {correctness:>6.3f} {_fmt_tokens(in_out):>7} {_fmt_tokens(cache):>7} {f'${cost:.3f}':>8} {wall:>6.1f}s {status:<8}"
        )

    # Summary
    summary = results.get("summary", {})
    if summary:
        lines.append(sep)
        total_cost = summary.get("total_cost_usd", 0)
        # Recompute in+out and cache from task data
        total_in_out = 0
        total_cache = 0
        for data in tasks.values():
            t = data.get("tokens") or {}
            total_in_out += t.get("input", 0) + t.get("output", 0)
            total_cache += t.get("cache_read", 0) + t.get("cache_write", 0)
        lines.append(
            f"{'TOTAL':<25} {summary.get('mean_correctness', 0):>6.3f} {_fmt_tokens(total_in_out):>7} {_fmt_tokens(total_cache):>7} "
            f"{f'${total_cost:.3f}':>8} {summary.get('total_wall_time_sec', 0):>6.1f}s "
            f"{summary.get('tasks_fully_solved', 0)}/{summary.get('tasks_attempted', 0)} solved"
        )

    return "\n".join(lines)

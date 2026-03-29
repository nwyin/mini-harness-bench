from __future__ import annotations


def format_results_table(results: dict) -> str:
    tasks = results.get("tasks", {})
    if not tasks:
        return "No task results."

    header = f"{'Task ID':<30} {'Correct':>8} {'Tokens':>8} {'Cost':>8} {'Time':>8} {'Status':<10}"
    sep = "-" * len(header)
    lines = [header, sep]

    for task_id, data in sorted(tasks.items()):
        correctness = data.get("correctness", 0.0)
        total_tokens = 0
        if data.get("tokens"):
            total_tokens = data["tokens"].get("input", 0) + data["tokens"].get("output", 0)
        cost = data.get("cost_usd", 0.0) or 0.0
        wall = data.get("wall_time_sec", {}).get("total", 0.0)
        timed_out = data.get("timed_out", False)

        if timed_out:
            status = "timeout"
        elif correctness >= 1.0:
            status = "passed"
        elif correctness > 0.0:
            status = "partial"
        else:
            status = "failed"

        lines.append(f"{task_id:<30} {correctness:>8.3f} {total_tokens:>8,} {f'${cost:.3f}':>8} {wall:>7.1f}s {status:<10}")

    # Summary
    summary = results.get("summary", {})
    if summary:
        lines.append(sep)
        total_cost = summary.get("total_cost_usd", 0)
        cost_str = f"${total_cost:.3f}"
        lines.append(
            f"{'TOTAL':<30} {summary.get('mean_correctness', 0):>8.3f} "
            f"{summary.get('total_tokens', 0):>8,} {cost_str:>8} "
            f"{summary.get('total_wall_time_sec', 0):>7.1f}s "
            f"{summary.get('tasks_fully_solved', 0)}/{summary.get('tasks_attempted', 0)} solved"
        )

    return "\n".join(lines)

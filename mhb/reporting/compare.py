from __future__ import annotations


def format_comparison_table(results_a: dict, results_b: dict) -> str:
    run_a = results_a.get("run_id", "run-A")
    run_b = results_b.get("run_id", "run-B")
    tasks_a = results_a.get("tasks", {})
    tasks_b = results_b.get("tasks", {})
    all_task_ids = sorted(set(tasks_a) | set(tasks_b))

    if not all_task_ids:
        return "No tasks to compare."

    header = f"{'Task ID':<30} {'Correct A':>10} {'Correct B':>10} {'Delta':>8} {'Cost A':>8} {'Cost B':>8}"
    sep = "-" * len(header)
    lines = [f"Comparing {run_a} vs {run_b}", "", header, sep]

    for task_id in all_task_ids:
        a = tasks_a.get(task_id, {})
        b = tasks_b.get(task_id, {})
        ca = a.get("correctness", 0.0)
        cb = b.get("correctness", 0.0)
        delta = cb - ca
        cost_a = a.get("cost_usd", 0.0) or 0.0
        cost_b = b.get("cost_usd", 0.0) or 0.0
        delta_str = f"{delta:+.3f}"
        lines.append(f"{task_id:<30} {ca:>10.3f} {cb:>10.3f} {delta_str:>8} {f'${cost_a:.3f}':>8} {f'${cost_b:.3f}':>8}")

    # Summary comparison
    sa = results_a.get("summary", {})
    sb = results_b.get("summary", {})
    lines.append(sep)
    mc_a = sa.get("mean_correctness", 0)
    mc_b = sb.get("mean_correctness", 0)
    lines.append(f"{'MEAN':<30} {mc_a:>10.3f} {mc_b:>10.3f} {mc_b - mc_a:>+8.3f}")

    return "\n".join(lines)

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mhb.reporting.compare import format_comparison_table
from mhb.reporting.display import format_results_table
from mhb.reporting.results import read_results
from mhb.tasks.loader import discover_tasks, filter_by_tier


def cmd_tasks_list(args: argparse.Namespace) -> None:
    tasks = discover_tasks()
    if not tasks:
        print("No tasks found.")
        return

    header = f"{'Task ID':<30} {'Category':<25} {'Difficulty':<12} {'Tier':<10}"
    print(header)
    print("-" * len(header))
    for t in tasks:
        print(f"{t.task_id:<30} {t.category:<25} {t.difficulty:<12} {t.tier:<10}")
    print(f"\n{len(tasks)} tasks total")


def cmd_run(args: argparse.Namespace) -> None:
    from mhb.harness import run_benchmark

    all_tasks = discover_tasks()
    if not all_tasks:
        print("No tasks found.", file=sys.stderr)
        sys.exit(1)

    if args.task:
        tasks = [t for t in all_tasks if t.task_id == args.task]
        if not tasks:
            print(f"Task not found: {args.task}", file=sys.stderr)
            sys.exit(1)
        tier = tasks[0].tier
    elif args.all:
        tasks = all_tasks
        tier = "full"
    else:
        tier = args.tier or "full"
        tasks = filter_by_tier(all_tasks, tier)

    if not tasks:
        print(f"No tasks for tier: {tier}", file=sys.stderr)
        sys.exit(1)

    print(f"Running {len(tasks)} tasks with agent={args.agent} model={args.model} tier={tier} concurrency={args.concurrency}")
    results = run_benchmark(
        agent_name=args.agent,
        model=args.model or "default",
        tasks=tasks,
        tier=tier,
        concurrency=args.concurrency,
    )
    print(f"\nRun ID: {results['run_id']}")
    print(format_results_table(results))


def cmd_results(args: argparse.Namespace) -> None:
    results_path = Path("results") / args.run_id / "results.json"
    if not results_path.exists():
        print(f"Results not found: {results_path}", file=sys.stderr)
        sys.exit(1)
    results = read_results(results_path)
    print(format_results_table(results))


def cmd_compare(args: argparse.Namespace) -> None:
    path_a = Path("results") / args.run_id_a / "results.json"
    path_b = Path("results") / args.run_id_b / "results.json"
    for p in [path_a, path_b]:
        if not p.exists():
            print(f"Results not found: {p}", file=sys.stderr)
            sys.exit(1)
    results_a = read_results(path_a)
    results_b = read_results(path_b)
    print(format_comparison_table(results_a, results_b))


def main() -> None:
    parser = argparse.ArgumentParser(prog="mhb", description="Mini Harness Bench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # tasks list
    tasks_parser = subparsers.add_parser("tasks", help="Task management")
    tasks_sub = tasks_parser.add_subparsers(dest="tasks_command", required=True)
    tasks_sub.add_parser("list", help="List available tasks")

    # run
    run_parser = subparsers.add_parser("run", help="Run benchmark")
    run_parser.add_argument("--agent", required=True, choices=["claude-code", "codex", "tau", "oracle"])
    run_parser.add_argument("--model", default=None)
    run_parser.add_argument("--task", default=None, help="Run a single task by ID")
    run_parser.add_argument("--tier", default=None, choices=["smoke", "standard", "full"])
    run_parser.add_argument("--all", action="store_true", help="Run all tasks")
    run_parser.add_argument("--concurrency", type=int, default=4)

    # results
    results_parser = subparsers.add_parser("results", help="Show results")
    results_parser.add_argument("run_id")

    # compare
    compare_parser = subparsers.add_parser("compare", help="Compare two runs")
    compare_parser.add_argument("run_id_a")
    compare_parser.add_argument("run_id_b")

    args = parser.parse_args()

    if args.command == "tasks":
        cmd_tasks_list(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "results":
        cmd_results(args)
    elif args.command == "compare":
        cmd_compare(args)


if __name__ == "__main__":
    main()

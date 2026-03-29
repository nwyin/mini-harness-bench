from __future__ import annotations

import datetime
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import yaml

from mhb.agents.base import BaseAgent
from mhb.evaluation.runner import run_evaluation
from mhb.reporting.results import write_results
from mhb.reporting.trajectory import write_trajectory
from mhb.scoring import compute_correctness, compute_cost, load_pricing
from mhb.tasks.loader import Task
from mhb.tasks.workspace import setup_workspace


def _get_agent(agent_name: str) -> BaseAgent:
    if agent_name == "oracle":
        from mhb.agents.oracle import OracleAgent

        return OracleAgent()
    elif agent_name == "claude-code":
        from mhb.agents.claude_code import ClaudeCodeAgent

        return ClaudeCodeAgent()
    elif agent_name == "tau":
        from mhb.agents.tau import TauAgent

        return TauAgent()
    elif agent_name == "codex":
        from mhb.agents.codex import CodexAgent

        return CodexAgent()
    else:
        raise ValueError(f"Unknown agent: {agent_name}")


def _load_tier_config() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "tiers.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return data.get("tiers", {})


def _get_timeout(task: Task, tier: str, tier_config: dict) -> int:
    if task.max_agent_time_sec:
        return task.max_agent_time_sec
    return tier_config.get(tier, {}).get("default_agent_timeout_sec", 300)


def run_single_task(
    agent_name: str,
    model: str,
    task: Task,
    tier: str,
    tier_config: dict,
    results_dir: Path,
    pricing: dict,
) -> dict:
    agent = _get_agent(agent_name)
    timeout = _get_timeout(task, tier, tier_config)

    # Setup workspace
    ws = setup_workspace(task)
    try:
        # Run agent
        agent_result = agent.run(
            instruction=task.instruction,
            workdir=ws.workdir,
            timeout=timeout,
            model=model,
            task_id=task.task_id,
        )

        # Run evaluation
        eval_result = run_evaluation(
            workdir=ws.workdir,
            task_dir=task.task_dir,
            venv_dir=ws.venv_dir,
        )

        # Score
        correctness = compute_correctness(eval_result.tests_passed, eval_result.tests_total)
        cost_usd = agent_result.cost_usd
        if cost_usd is None and agent_result.tokens:
            cost_usd = compute_cost(agent_result.tokens, model, pricing)

        # Write trajectory
        traj_path = results_dir / "trajectories" / f"{task.task_id}.jsonl"
        write_trajectory(agent_result.trajectory_events, traj_path)

        # Determine failure mode
        failure_mode = None
        if agent_result.timed_out:
            failure_mode = "timeout"
        elif agent_result.exit_code != 0:
            failure_mode = "agent_error"
        elif correctness < 1.0:
            failure_mode = "incorrect"

        return {
            "correctness": correctness,
            "tests_passed": eval_result.tests_passed,
            "tests_total": eval_result.tests_total,
            "test_details": eval_result.test_details,
            "tokens": agent_result.tokens,
            "cost_usd": cost_usd or 0.0,
            "wall_time_sec": {
                "agent": agent_result.wall_time_sec,
                "test": eval_result.wall_time_sec,
                "total": agent_result.wall_time_sec + eval_result.wall_time_sec,
            },
            "timed_out": agent_result.timed_out,
            "max_agent_time_sec": timeout,
            "failure_mode": failure_mode,
        }
    finally:
        ws.cleanup()


def run_benchmark(
    agent_name: str,
    model: str,
    tasks: list[Task],
    tier: str,
    concurrency: int = 4,
) -> dict:
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    results_dir = Path(os.environ.get("MHB_RESULTS_DIR", "results")) / run_id
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "trajectories").mkdir(exist_ok=True)

    tier_config = _load_tier_config()
    pricing = load_pricing()

    task_results = {}

    if concurrency <= 1:
        for task in tasks:
            task_results[task.task_id] = run_single_task(agent_name, model, task, tier, tier_config, results_dir, pricing)
    else:
        with ProcessPoolExecutor(max_workers=concurrency) as executor:
            futures = {}
            for task in tasks:
                f = executor.submit(run_single_task, agent_name, model, task, tier, tier_config, results_dir, pricing)
                futures[f] = task.task_id
            for future in as_completed(futures):
                task_id = futures[future]
                try:
                    task_results[task_id] = future.result()
                except Exception as e:
                    task_results[task_id] = {
                        "correctness": 0.0,
                        "tests_passed": 0,
                        "tests_total": 0,
                        "test_details": [],
                        "tokens": None,
                        "cost_usd": 0.0,
                        "wall_time_sec": {"agent": 0, "test": 0, "total": 0},
                        "timed_out": False,
                        "max_agent_time_sec": 0,
                        "failure_mode": f"harness_error: {e}",
                    }

    # Compute summary
    attempted = len(task_results)
    fully_solved = sum(1 for r in task_results.values() if r["correctness"] >= 1.0)
    timed_out = sum(1 for r in task_results.values() if r.get("timed_out", False))
    mean_correctness = sum(r["correctness"] for r in task_results.values()) / attempted if attempted else 0.0
    total_cost = sum(r.get("cost_usd", 0) or 0 for r in task_results.values())
    total_tokens = 0
    for r in task_results.values():
        if r.get("tokens"):
            total_tokens += r["tokens"].get("input", 0) + r["tokens"].get("output", 0)
    total_wall = sum(r["wall_time_sec"]["total"] for r in task_results.values())

    results = {
        "run_id": run_id,
        "agent": agent_name,
        "model": model,
        "timestamp": datetime.datetime.now().isoformat(),
        "config": {
            "tier": tier,
            "concurrency": concurrency,
            "default_agent_timeout_sec": tier_config.get(tier, {}).get("default_agent_timeout_sec", 300),
        },
        "tasks": task_results,
        "summary": {
            "mean_correctness": mean_correctness,
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "tasks_attempted": attempted,
            "tasks_fully_solved": fully_solved,
            "tasks_timed_out": timed_out,
            "total_wall_time_sec": total_wall,
        },
    }

    write_results(results, results_dir / "results.json")
    return results

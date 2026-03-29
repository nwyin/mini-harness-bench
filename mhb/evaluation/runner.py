from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from mhb.evaluation.parser import parse_pytest_output, parse_shell_checks


@dataclass
class EvalResult:
    test_details: list[dict]
    tests_passed: int
    tests_total: int
    wall_time_sec: float


def run_evaluation(workdir: Path, task_dir: Path, venv_dir: Path) -> EvalResult:
    start = time.monotonic()
    test_details = []

    # Find tests: prefer task_dir/tests/ (hidden from agent), fall back to workdir/tests/ (visible to agent)
    tests_dir = task_dir / "tests"
    if not tests_dir.exists() or not any(tests_dir.glob("test_*.py")):
        tests_dir = workdir / "tests"

    if tests_dir.exists() and any(tests_dir.glob("test_*.py")):
        python = str(venv_dir / "bin" / "python")
        env = {
            **os.environ,
            "VIRTUAL_ENV": str(venv_dir),
            "PATH": f"{venv_dir / 'bin'}:{os.environ['PATH']}",
            "PYTHONPATH": str(workdir),
            "MHB_TASK_DIR": str(task_dir),
        }
        proc = subprocess.run(
            [python, "-m", "pytest", str(tests_dir), "-v", "--tb=short", "--no-header"],
            cwd=workdir,
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
        test_details.extend(parse_pytest_output(proc.stdout))

    # Run shell checks if present
    check_script = task_dir / "tests" / "check.sh"
    if check_script.exists():
        env = {
            **os.environ,
            "VIRTUAL_ENV": str(venv_dir),
            "PATH": f"{venv_dir / 'bin'}:{os.environ['PATH']}",
            "MHB_TASK_DIR": str(task_dir),
        }
        proc = subprocess.run(
            ["bash", str(check_script)],
            cwd=workdir,
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        test_details.extend(parse_shell_checks(proc.stdout))

    elapsed = time.monotonic() - start
    passed = sum(1 for t in test_details if t["status"] == "passed")
    return EvalResult(
        test_details=test_details,
        tests_passed=passed,
        tests_total=len(test_details),
        wall_time_sec=elapsed,
    )

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from mhb.tasks.loader import Task

CACHE_DIR = Path(os.environ.get("MHB_CACHE_DIR", Path.home() / ".cache" / "mhb" / "venvs"))


def _hash_file(path: Path) -> str:
    if not path.exists():
        return "empty"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


@dataclass
class TaskWorkspace:
    task: Task
    workdir: Path
    venv_dir: Path

    def cleanup(self) -> None:
        if self.workdir.exists():
            shutil.rmtree(self.workdir, ignore_errors=True)


def setup_workspace(task: Task, keep_workdir: bool = False) -> TaskWorkspace:
    workdir = Path(tempfile.mkdtemp(prefix=f"mhb-{task.task_id}-"))

    # Copy workspace files
    if task.workspace_dir.exists():
        shutil.copytree(task.workspace_dir, workdir, dirs_exist_ok=True)

    # Git init for audit trail
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "mhb",
        "GIT_AUTHOR_EMAIL": "mhb@bench",
        "GIT_COMMITTER_NAME": "mhb",
        "GIT_COMMITTER_EMAIL": "mhb@bench",
    }
    subprocess.run(["git", "init", "-q"], cwd=workdir, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=workdir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "initial", "--allow-empty"],
        cwd=workdir,
        check=True,
        capture_output=True,
        env=git_env,
    )

    # Create venv in workdir (always fresh — uv venv creation is fast ~200ms)
    venv_dir = workdir / ".venv"
    subprocess.run(["uv", "venv", str(venv_dir), "-q", "--python", "3.12"], cwd=workdir, check=True, capture_output=True)

    # Install pytest into the venv (needed for evaluation)
    venv_env = {**os.environ, "VIRTUAL_ENV": str(venv_dir), "PATH": f"{venv_dir / 'bin'}:{os.environ['PATH']}"}
    subprocess.run(["uv", "pip", "install", "pytest", "-q"], cwd=workdir, check=True, capture_output=True, env=venv_env)

    # Run task-specific setup if present
    setup_script = task.task_dir / "setup.sh"
    if setup_script.exists():
        subprocess.run(["bash", str(setup_script)], cwd=workdir, check=True, capture_output=True, env=venv_env)

    return TaskWorkspace(task=task, workdir=workdir, venv_dir=venv_dir)

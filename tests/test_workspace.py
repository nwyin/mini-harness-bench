import subprocess
import tempfile
from pathlib import Path

from mhb.tasks.loader import Task
from mhb.tasks.workspace import setup_workspace


def _make_task(tmp_path: Path) -> Task:
    """Create a minimal task for testing workspace setup."""
    task_dir = tmp_path / "test-task"
    task_dir.mkdir()
    workspace = task_dir / "workspace"
    workspace.mkdir()
    (workspace / "hello.py").write_text("print('hello')\n")

    return Task(
        task_id="test-task",
        instruction="test",
        category="test",
        difficulty="easy",
        tier="smoke",
        task_dir=task_dir,
    )


def test_workspace_creates_workdir():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(Path(tmp))
        ws = setup_workspace(task)
        try:
            assert ws.workdir.exists()
            assert (ws.workdir / "hello.py").exists()
        finally:
            ws.cleanup()


def test_workspace_has_git():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(Path(tmp))
        ws = setup_workspace(task)
        try:
            result = subprocess.run(["git", "log", "--oneline"], cwd=ws.workdir, capture_output=True, text=True)
            assert result.returncode == 0
            assert "initial" in result.stdout
        finally:
            ws.cleanup()


def test_workspace_has_venv():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(Path(tmp))
        ws = setup_workspace(task)
        try:
            assert ws.venv_dir.exists()
            assert (ws.venv_dir / "bin" / "python").exists()
        finally:
            ws.cleanup()


def test_workspace_cleanup():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(Path(tmp))
        ws = setup_workspace(task)
        workdir = ws.workdir
        ws.cleanup()
        assert not workdir.exists()

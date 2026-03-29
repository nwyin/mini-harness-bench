from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from mhb.agents.base import AgentResult, BaseAgent


class OracleAgent(BaseAgent):
    name = "oracle"

    def run(self, instruction: str, workdir: Path, timeout: int, model: str | None = None, task_id: str | None = None) -> AgentResult:
        start = time.monotonic()

        if task_id is None:
            return AgentResult(exit_code=1, stderr="oracle requires task_id")

        tasks_root = Path(os.environ.get("MHB_TASKS_DIR", Path(__file__).parent.parent.parent / "tasks"))
        reference_dir = tasks_root / task_id / "reference"

        if not reference_dir.exists():
            return AgentResult(exit_code=1, stderr=f"No reference dir: {reference_dir}")

        # If reference contains a .sh script, run it instead of copying
        sh_files = list(reference_dir.glob("*.sh"))
        if sh_files and not any(f.suffix == ".py" for f in reference_dir.iterdir()):
            # Reference is script-based — execute all .sh files
            for sh_file in sh_files:
                subprocess.run(
                    ["bash", str(sh_file)],
                    cwd=workdir,
                    capture_output=True,
                    timeout=timeout,
                )
        else:
            # Copy reference solution files into workdir
            for item in reference_dir.iterdir():
                dest = workdir / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)

        # Run reference setup.sh if it exists
        ref_setup = reference_dir / "setup.sh"
        if ref_setup.exists() and ref_setup not in sh_files:
            venv_dir = workdir / ".venv"
            env = {**os.environ, "VIRTUAL_ENV": str(venv_dir), "PATH": f"{venv_dir / 'bin'}:{os.environ['PATH']}"}
            subprocess.run(["bash", str(ref_setup)], cwd=workdir, capture_output=True, env=env)

        elapsed = time.monotonic() - start
        return AgentResult(wall_time_sec=elapsed, tokens=None, cost_usd=0.0)

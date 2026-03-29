from __future__ import annotations

import subprocess
import time
from pathlib import Path

from mhb.agents.base import AgentResult, BaseAgent


class CodexAgent(BaseAgent):
    name = "codex"

    def run(self, instruction: str, workdir: Path, timeout: int, model: str | None = None, task_id: str | None = None) -> AgentResult:
        cmd = ["codex", "exec", "--sandbox", "danger-full-access"]
        if model:
            cmd.extend(["--model", model])
        cmd.extend(["--", instruction])

        start = time.monotonic()
        try:
            proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired as e:
            elapsed = time.monotonic() - start
            return AgentResult(
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                exit_code=-1,
                timed_out=True,
                wall_time_sec=elapsed,
            )
        elapsed = time.monotonic() - start

        return AgentResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            timed_out=timed_out,
            wall_time_sec=elapsed,
        )

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from pathlib import Path

from mhb.agents.base import AgentResult, BaseAgent

FEEDBACK_SUFFIX = """

After completing your work, verify by running: python -m pytest tests/ -v
If tests fail, fix the issues and re-run. Once all tests pass, stop immediately."""


class CodexAgent(BaseAgent):
    name = "codex"

    def run(self, instruction: str, workdir: Path, timeout: int, model: str | None = None, task_id: str | None = None) -> AgentResult:
        full_instruction = instruction.strip() + FEEDBACK_SUFFIX

        cmd = ["codex", "exec", "--sandbox", "danger-full-access"]
        if model:
            cmd.extend(["--model", model])
        cmd.extend(["--", full_instruction])

        start = time.monotonic()
        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []

        proc = subprocess.Popen(
            cmd,
            cwd=workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,
        )

        def _read_stream(stream, chunks):
            for line in stream:
                chunks.append(line)

        stdout_thread = threading.Thread(target=_read_stream, args=(proc.stdout, stdout_chunks))
        stderr_thread = threading.Thread(target=_read_stream, args=(proc.stderr, stderr_chunks))
        stdout_thread.start()
        stderr_thread.start()

        try:
            proc.wait(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=5)
            timed_out = True

        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)

        elapsed = time.monotonic() - start
        stdout = "".join(stdout_chunks)
        stderr = "".join(stderr_chunks)

        return AgentResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode or 0,
            timed_out=timed_out,
            wall_time_sec=elapsed,
        )

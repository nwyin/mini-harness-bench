from __future__ import annotations

import json
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


class ClaudeCodeAgent(BaseAgent):
    name = "claude-code"

    def run(self, instruction: str, workdir: Path, timeout: int, model: str | None = None, task_id: str | None = None) -> AgentResult:
        full_instruction = instruction.strip() + FEEDBACK_SUFFIX

        cmd = [
            "claude",
            "-p",
            full_instruction,
            "--output-format",
            "stream-json",
            "--verbose",
            "--allowedTools",
            "Edit,Write,Bash,Read,Glob,Grep",
            "--max-turns",
            "50",
            "--dangerously-skip-permissions",
        ]
        if model:
            cmd.extend(["--model", model])

        start = time.monotonic()
        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []

        proc = subprocess.Popen(
            cmd,
            cwd=workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            # Start in new process group so we can kill the whole tree on timeout
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
            # Kill the entire process group
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=5)
            timed_out = True

        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)

        elapsed = time.monotonic() - start
        stdout = "".join(stdout_chunks)
        stderr = "".join(stderr_chunks)

        events = _parse_stream_json(stdout)
        tokens = _extract_tokens(events)
        return AgentResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode or 0,
            timed_out=timed_out,
            wall_time_sec=elapsed,
            tokens=tokens,
            trajectory_events=events,
        )


def _parse_stream_json(output: str) -> list[dict]:
    events = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _extract_tokens(events: list[dict]) -> dict | None:
    total = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    found = False
    for ev in events:
        usage = ev.get("usage") or ev.get("message", {}).get("usage")
        if usage:
            found = True
            total["input"] += usage.get("input_tokens", 0)
            total["output"] += usage.get("output_tokens", 0)
            total["cache_read"] += usage.get("cache_read_input_tokens", usage.get("cache_creation_input_tokens", 0))
            total["cache_write"] += usage.get("cache_creation_input_tokens", 0)
    return total if found else None

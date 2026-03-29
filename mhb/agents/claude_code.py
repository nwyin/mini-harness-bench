from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from mhb.agents.base import AgentResult, BaseAgent

FEEDBACK_SUFFIX = """

After completing your work, verify it by running the tests:
  python -m pytest tests/ -v
If any tests fail, read the error output carefully, fix the issues, and re-run until all tests pass.
Do not stop until all tests pass or you've exhausted your attempts."""


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
            "--permission-mode",
            "bypassPermissions",
        ]
        if model:
            cmd.extend(["--model", model])

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
                trajectory_events=_parse_stream_json(e.stdout.decode() if e.stdout else ""),
            )
        elapsed = time.monotonic() - start

        events = _parse_stream_json(proc.stdout)
        tokens = _extract_tokens(events)
        return AgentResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
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

from __future__ import annotations

import json
from pathlib import Path

from mhb.agents.base import AgentResult, BaseAgent
from mhb.agents.subprocess_util import run_with_streaming


class CodexAgent(BaseAgent):
    name = "codex"

    def run(self, instruction: str, workdir: Path, timeout: int, model: str | None = None, task_id: str | None = None) -> AgentResult:
        cmd = ["codex", "exec", "--json", "--sandbox", "danger-full-access"]
        if model:
            cmd.extend(["--model", model])
        cmd.extend(["--", instruction])

        stdout, stderr, rc, timed_out, elapsed = run_with_streaming(cmd, workdir, timeout)

        events = _parse_jsonl(stdout)
        tokens = _extract_tokens(events)

        return AgentResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=rc,
            timed_out=timed_out,
            wall_time_sec=elapsed,
            tokens=tokens,
            trajectory_events=events,
        )


def _parse_jsonl(output: str) -> list[dict]:
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
        usage = ev.get("usage")
        if usage:
            found = True
            total["input"] += usage.get("input_tokens", 0)
            total["output"] += usage.get("output_tokens", 0)
            total["cache_read"] += usage.get("cached_input_tokens", 0)
    return total if found else None

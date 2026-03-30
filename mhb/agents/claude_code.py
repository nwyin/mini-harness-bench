from __future__ import annotations

import json
from pathlib import Path

from mhb.agents.base import AgentResult, BaseAgent
from mhb.agents.subprocess_util import run_with_streaming


class ClaudeCodeAgent(BaseAgent):
    name = "claude-code"

    def run(self, instruction: str, workdir: Path, timeout: int, model: str | None = None, task_id: str | None = None) -> AgentResult:
        cmd = [
            "claude",
            "-p",
            instruction,
            "--output-format",
            "stream-json",
            "--verbose",
            "--allowedTools",
            "Edit,Write,Bash,Read,Glob,Grep",
            "--max-turns",
            "20",
            "--dangerously-skip-permissions",
        ]
        if model:
            cmd.extend(["--model", model])

        stdout, stderr, rc, timed_out, elapsed = run_with_streaming(cmd, workdir, timeout)

        events = _parse_stream_json(stdout)
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
    # Prefer the 'result' event which has true totals (per-turn events are duplicated in stream-json)
    for ev in reversed(events):
        if ev.get("type") == "result":
            usage = ev.get("usage")
            if usage:
                return {
                    "input": usage.get("input_tokens", 0),
                    "output": usage.get("output_tokens", 0),
                    "cache_read": usage.get("cache_read_input_tokens", 0),
                    "cache_write": usage.get("cache_creation_input_tokens", 0),
                }

    # Fallback: deduplicate per-turn events and sum
    seen = set()
    total = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    found = False
    for ev in events:
        usage = ev.get("usage") or ev.get("message", {}).get("usage")
        if usage:
            key = (usage.get("input_tokens"), usage.get("output_tokens"), usage.get("cache_read_input_tokens"))
            if key in seen:
                continue
            seen.add(key)
            found = True
            total["input"] += usage.get("input_tokens", 0)
            total["output"] += usage.get("output_tokens", 0)
            total["cache_read"] += usage.get("cache_read_input_tokens", 0)
            total["cache_write"] += usage.get("cache_creation_input_tokens", 0)
    return total if found else None

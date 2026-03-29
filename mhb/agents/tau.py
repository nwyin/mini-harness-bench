from __future__ import annotations

import json
import tempfile
from pathlib import Path

from mhb.agents.base import AgentResult, BaseAgent
from mhb.agents.subprocess_util import run_with_streaming


class TauAgent(BaseAgent):
    name = "tau"

    def run(self, instruction: str, workdir: Path, timeout: int, model: str | None = None, task_id: str | None = None) -> AgentResult:
        trace_dir = Path(tempfile.mkdtemp(prefix="mhb-tau-trace-"))
        stats_path = trace_dir / "tau-stats.json"

        cmd = [
            "tau",
            "--prompt",
            instruction,
            "--tools",
            "bash,file_read,file_write,file_edit,grep,glob",
            "--trace-output",
            str(trace_dir),
            "--stats-json",
            str(stats_path),
            "--no-session",
            "--yolo",
        ]
        if model:
            cmd.extend(["--model", model])
        if task_id:
            cmd.extend(["--task-id", task_id])

        stdout, stderr, rc, timed_out, elapsed = run_with_streaming(cmd, workdir, timeout)

        events = _parse_trace_jsonl(trace_dir / "trace.jsonl")
        tokens, cost = _parse_run_json(trace_dir / "run.json")

        return AgentResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=rc,
            timed_out=timed_out,
            wall_time_sec=elapsed,
            tokens=tokens,
            cost_usd=cost,
            trajectory_events=events,
        )


def _parse_trace_jsonl(path: Path) -> list[dict]:
    events = []
    if not path.exists():
        return events
    for line in path.read_text().strip().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _parse_run_json(path: Path) -> tuple[dict | None, float | None]:
    if not path.exists():
        return None, None
    try:
        data = json.loads(path.read_text())
        tokens = {
            "input": data.get("total_input_tokens", 0),
            "output": data.get("total_output_tokens", 0),
        }
        cost = data.get("total_cost")
        return tokens, cost
    except (json.JSONDecodeError, KeyError):
        return None, None

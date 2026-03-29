# Mini Harness Bench — Implementation Spec

Read `SPEC.md` for full requirements. This document specifies implementation details and phasing.

## Verification (all phases)

```bash
uv run pytest tests/ -v && uvx ruff check .
```

---

## Phase 1: Harness Infrastructure + 5 Smoke Tasks

### Requirements

#### Project setup
- `pyproject.toml`: name=`mini-harness-bench`, python>=3.12, dep=`pyyaml>=6.0`, script entry `mhb = "mhb.cli:main"`
- `.python-version`: `3.12`
- `.gitignore`: `results/`, `__pycache__/`, `.venv/`, `*.egg-info/`, `~/.cache/mhb/`
- `config/pricing.yaml`: token costs for Anthropic (claude-sonnet-4, claude-opus-4, claude-haiku) and OpenAI (gpt-4o, o3, o4-mini) models
- `config/tiers.yaml`: smoke/standard/full tier definitions with task lists and default timeouts

#### CLI (`mhb/cli.py`)
- `argparse`-based, subcommands: `run`, `tasks`, `results`, `compare`
- `mhb tasks list` — prints table: task_id, category, difficulty, tier
- `mhb run --agent <agent> --model <model> [--task <id>] [--tier <tier>] [--all] [--concurrency <n>]`
  - `--concurrency` defaults to 4
  - `--tier` defaults to `full`
  - Exactly one of `--task`, `--tier`, or `--all` must be specified
- `mhb results <run-id>` — prints summary table from results.json
- `mhb compare <run-id-1> <run-id-2>` — prints side-by-side delta table
- All tables are plain text with aligned columns (no `rich` dependency)

#### Task loader (`mhb/tasks/loader.py`)
- Discover all `tasks/*/task.yaml` files
- Parse task.yaml fields: `instruction`, `category`, `tags`, `difficulty`, `tier`, `max_agent_time_sec`, `expert_time_estimate_min`
- Filter by tier: return tasks where task.tier is included in the requested tier (smoke < standard < full, i.e. smoke tasks are included in standard and full)
- Return list of `Task` dataclasses

#### Workspace setup (`mhb/tasks/workspace.py`)
- For each task run:
  1. Create temp directory
  2. Copy `tasks/<id>/workspace/*` into it
  3. `git init` + `git add -A` + `git commit -m "initial"`
  4. Create uv venv in the temp dir
  5. If `tasks/<id>/setup.sh` exists, run it in the temp dir with the venv activated
- Venv caching: hash `setup.sh` content (or "empty" if absent). Cache venvs at `~/.cache/mhb/venvs/<task-id>-<hash>/`. If cache hit, copy instead of creating fresh + running setup.sh.
- Cleanup: remove temp dir after scoring (unless `--keep-workdirs` flag)

#### Agent base (`mhb/agents/base.py`)
- Abstract base class with method: `run(instruction: str, workdir: Path, timeout: int) -> AgentResult`
- `AgentResult` dataclass: `stdout: str`, `stderr: str`, `exit_code: int`, `timed_out: bool`, `wall_time_sec: float`, `tokens: dict | None`, `cost_usd: float | None`, `trajectory_events: list[dict]`

#### Oracle agent (`mhb/agents/oracle.py`)
- Copies `tasks/<id>/reference/*` into workdir (overwriting workspace files)
- If `setup.sh` exists in reference/, runs it
- Returns AgentResult with zero tokens/cost, wall_time = copy duration
- No trajectory events (oracle doesn't use an LLM)

#### Evaluation runner (`mhb/evaluation/runner.py`)
- Run `uv run pytest <task-tests-dir> -v --tb=short --no-header -q` in the task workdir
- The pytest invocation must be able to find hidden test data: pass `--rootdir` or set env var `MHB_TASK_DIR` pointing to the original `tasks/<id>/` directory so tests can access `tests/data/`
- Capture stdout/stderr, parse results

#### Evaluation parser (`mhb/evaluation/parser.py`)
- Parse pytest `-v` output to extract: test name, passed/failed status
- Compute correctness = passed / total
- If shell check `tests/check.sh` exists, run it and parse structured output (lines of `PASS: <name>` or `FAIL: <name>`)

#### Scoring (`mhb/scoring.py`)
- Combine pytest results + shell check results
- Compute per-task: `correctness`, `tests_passed`, `tests_total`, `test_details`
- Compute cost from tokens + pricing.yaml lookup

#### Harness orchestrator (`mhb/harness.py`)
- Given agent, model, task list, concurrency:
  1. Generate run_id (timestamp-based, e.g. `20260329-143022`)
  2. Create `results/<run-id>/` and `results/<run-id>/trajectories/`
  3. For each task (parallel via `concurrent.futures.ProcessPoolExecutor`):
     a. Setup workspace (copy, git init, venv)
     b. Run agent with timeout (from tier config or task.yaml override)
     c. Run evaluation (pytest + shell checks)
     d. Score results
     e. Write trajectory JSONL to `results/<run-id>/trajectories/<task-id>.jsonl`
     f. Cleanup workspace
  4. Write `results/<run-id>/results.json` with per-task scores and summary

#### Reporting (`mhb/reporting/`)
- `results.py`: write/read results.json matching the schema in SPEC.md
- `trajectory.py`: write JSONL trajectory files (one event per line with timestamp, type, content)
- `display.py`: format results as plain text table for `mhb results`
- `compare.py`: load two results.json, compute deltas, format as plain text table for `mhb compare`

#### Initial 5 smoke tasks
Create these task directories under `tasks/` with full `task.yaml`, `workspace/`, `tests/`, and `reference/`:

1. **fix-git**: workspace is a git repo with a deleted branch that needs recovery via reflog. Tests verify the branch exists and contains expected content.
2. **implement-from-tests**: workspace has only `tests/test_calculator.py` with tests for a Calculator class. Agent must create `calculator.py`. Reference solution is the working implementation.
3. **fix-off-by-one**: workspace has `process_data.py` with 3 functions containing off-by-one errors. Tests check edge cases (empty lists, single elements, boundaries).
4. **pandas-etl**: workspace has `input.csv` and instructions to transform it. `setup.sh` installs pandas. Tests verify output CSV content. Hidden test data in `tests/data/` with edge-case CSVs.
5. **heterogeneous-dates**: workspace has `dates.txt` with mixed date formats. Agent writes `normalize.py` to convert all to ISO 8601. Tests check output against expected. Hidden test data in `tests/data/`.

#### Harness unit tests (`tests/`)
- `test_loader.py`: task discovery, yaml parsing, tier filtering
- `test_scoring.py`: correctness computation, partial credit
- `test_results.py`: results.json serialization/deserialization
- `test_parser.py`: pytest output parsing
- `test_workspace.py`: temp dir creation, git init, cleanup

### Success Criteria

- `uv run pytest tests/ -v` passes
- `uvx ruff check .` passes
- `uv run mhb tasks list` prints 5 tasks with correct metadata
- `uv run mhb run --agent oracle --task implement-from-tests` produces results.json with correctness 1.0
- `uv run mhb run --agent oracle --tier smoke` runs all 5 tasks, all with correctness >= 0.95

---

## Phase 2: Agent Adapters (Claude Code + Tau + Codex)

### Prerequisites
- Phase 1 complete and passing

### Requirements

#### Claude Code adapter (`mhb/agents/claude_code.py`)
- Invoke: `claude -p <instruction> --output-format stream-json --allowedTools "Edit,Write,Bash,Read,Glob,Grep" --max-turns 50`
- Run as subprocess in task workdir with timeout
- Parse stream-json lines: extract tool_use events, result events, usage (input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens)
- Build trajectory events from parsed stream
- Compute cost via pricing.yaml lookup

#### Tau adapter (`mhb/agents/tau.py`)
- Invoke: `tau --prompt <instruction> --model <model> --tools bash,file_read,file_write,file_edit,grep,glob --trace-output <dir> --stats-json <path> --no-session --yolo --task-id <id>`
- Run as subprocess in task workdir with timeout
- Parse `<dir>/run.json` for: total_input_tokens, total_output_tokens, total_cost, wall_clock_ms, final_status, turns
- Parse `<dir>/trace.jsonl` for trajectory events
- Parse `<path>` (stats-json) for per-model cost breakdown

#### Codex adapter (`mhb/agents/codex.py`)
- Invoke: `codex exec --sandbox danger-full-access --model <model> -- <instruction>`
- Run as subprocess in task workdir with timeout
- Parse stdout for trajectory (Codex output format TBD — stub parsing, capture raw output)

### Success Criteria

- `uv run pytest tests/ -v` passes (add tests for adapter output parsing with fixture data)
- `uvx ruff check .` passes
- `uv run mhb run --agent claude-code --model claude-sonnet-4-20250514 --task implement-from-tests` completes and produces results
- `uv run mhb run --agent tau --model claude-sonnet-4-6 --task implement-from-tests` completes and produces results

---

## Phase 3: Remaining 19 Tasks

### Prerequisites
- Phase 1 and 2 complete and passing

### Requirements

Author remaining 19 task directories (6 standard-only + 8 full-only + 5 remaining smoke tasks) with full task.yaml, workspace/, tests/, and reference/.

See SPEC.md "Curated Task List" for the complete list and descriptions.

Each task must have:
- `task.yaml` with all required fields
- `workspace/` with initial files
- `tests/test_*.py` with pytest tests (3-8 tests per task for partial credit)
- `reference/` with a working solution that passes all tests
- `setup.sh` if the task needs deps beyond stdlib
- `tests/data/` for hidden test inputs where applicable (5+ tasks)

### Success Criteria

- `uv run mhb tasks list` shows 24 tasks
- `uv run pytest tests/ -v` passes
- `uvx ruff check .` passes
- `uv run mhb run --agent oracle --all` completes with correctness >= 0.95 on every task

---

## Phase 4: Reporting Polish

### Prerequisites
- Phases 1-3 complete

### Requirements

- `mhb results <run-id>` prints aligned plain text table: task_id, correctness, tokens, cost_usd, wall_time, status (passed/partial/failed/timeout)
- `mhb compare <run-id-1> <run-id-2>` prints side-by-side table with deltas (correctness diff, cost diff, time diff)
- Summary line at bottom of results table: mean correctness, total cost, total tokens, tasks solved/attempted

### Success Criteria

- `uv run mhb results <run-id>` exits 0 with readable tabular output
- `uv run mhb compare <run-id-1> <run-id-2>` exits 0 with delta table
- `uv run pytest tests/ -v` passes
- `uvx ruff check .` passes

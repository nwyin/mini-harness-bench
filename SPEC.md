# Mini Harness Bench

A focused benchmark for evaluating AI coding agents (Claude Code, Codex, Tau) on software engineering, debugging, data science, and devops tasks. Designed for **fast, frequent runs** — a smoke suite completes in ~4 minutes at 4x parallelism, making it practical to run hourly after a hacking session.

Loosely inspired by [Terminal-Bench](https://github.com/terminal-bench/terminal-bench).

---

## Spec 1: Core Harness Infrastructure

### Requirements

- Python 3.12+ project managed with `uv`, CLI via `argparse`
- CLI command: `mhb run --agent <agent> --model <model> [--task <task-id>] [--tier <tier>] [--all]`
- CLI command: `mhb run --concurrency <n>` (default 4) for parallel task execution
- CLI command: `mhb tasks list` to show available tasks
- CLI command: `mhb results <run-id>` to display results from a completed run
- Each task runs in an isolated git worktree under a temp directory, with its own `uv` venv
- **Parallel execution** via `concurrent.futures.ProcessPoolExecutor` — each task is fully isolated in its own worktree + venv, so concurrency is safe by default
- **Venv caching**: cache venvs per task in `~/.cache/mhb/venvs/<task-id>-<deps-hash>/`. On run, copy cached venv into worktree. Only rebuild if `setup.sh` or deps change. Saves 10-30s per task on warm runs.
- **Agent timeout enforcement**: hard per-task timeout (default from tier config, overridable per-task via `max_agent_time_sec` in `task.yaml`). Kill agent process on timeout. Score whatever tests pass at that point (partial credit). This is the most important lever for fast runs.

#### Agent Adapters

Four agent adapters, each using native tooling:

- **Claude Code**: invoke via `claude -p <instruction> --output-format stream-json --allowedTools "Edit,Write,Bash,Read,Glob,Grep" --max-turns 50`
  - Parse stream-json lines for trajectory, token counts (input_tokens, output_tokens, cache_read, cache_write), cost
- **Codex**: invoke via `codex exec --sandbox danger-full-access --model <model> -- <instruction>`
  - Parse output for trajectory
- **Tau**: invoke via `tau --prompt <instruction> --model <model> --tools bash,file_read,file_write,file_edit,grep,glob --trace-output <dir> --stats-json <path> --no-session --yolo --task-id <id>`
  - Parse `run.json` for summary (tokens, cost, wall_clock_ms, final_status, turns)
  - Parse `trace.jsonl` for trajectory events (tool_start/end, turn_start/end, agent_start/end)
  - Use `--stats-json` for aggregated token/cost breakdown by model and provider
- **Oracle**: copies `reference/` solution into worktree, runs `setup.sh` if present, then runs tests

#### Output and Tracking

- All agent output (stream-json for Claude, trace.jsonl for Tau, equivalent for Codex) is captured to a JSONL trajectory file per task per run
- Token counts and cost extracted from agent JSON output
- Wall-clock time tracked per task (agent phase + test phase separately)
- Evaluation runs pytest + optional shell checks after agent completes
- Scoring is multi-dimensional per task:
  - **Correctness**: `passed_tests / total_tests` (float 0.0-1.0)
  - **Cost**: total tokens (input + output), estimated USD based on model pricing
- Results written to `results/<run-id>/results.json` (structured summary) and `results/<run-id>/trajectories/<task-id>.jsonl` (full agent trajectory)
- Tasks are git repos: agent works in a worktree, all commands/file edits captured in git history for post-hoc audit

### Success Criteria

- `uv run mhb tasks list` prints available tasks with id, category, difficulty, tier
- `uv run mhb run --agent claude-code --model claude-sonnet-4-20250514 --task <any-task-id>` runs a task end-to-end and produces results.json + trajectory JSONL
- `uv run mhb run --agent tau --model claude-sonnet-4-6 --tier smoke --concurrency 4` completes in <10 minutes
- `uv run mhb results <run-id>` prints a summary table with correctness score, token count, cost, and wall time per task
- `uv run pytest tests/ -v` passes
- `uvx ruff check .` passes
- Trajectory JSONL contains every tool call / turn from the agent with timestamps
- Agent timeout kills the process and scores partial credit

### Verification

- `uv run pytest tests/ -v`
- `uvx ruff check .`
- `uv run mhb tasks list` exits 0
- `uv run mhb run --agent claude-code --task <task-id> --model claude-sonnet-4-20250514` completes and writes results
- `uv run mhb run --agent tau --task <task-id> --model claude-sonnet-4-6` completes and writes results

---

## Spec 2: Task Framework and Curated Tasks

### Requirements

#### Task Definition Format

Each task is a directory under `tasks/<task-id>/` containing:
- `task.yaml`: instruction (markdown), category, tags, difficulty, tier, max_agent_time_sec, expert_time_estimate_min
- `tests/`: pytest files and/or shell check scripts
- `tests/data/`: hidden test inputs (not copied to agent worktree — invisible to agent, accessible during pytest)
- `setup.sh`: optional setup script (install deps, seed data, create files) — replaces Docker
- `reference/`: reference solution (for oracle/validation runs)
- `workspace/`: initial files the agent starts with (copied into worktree)

#### Task Selection Criteria

All tasks must satisfy:
- Expert time estimate <10 min
- No network access required (no downloads, no API calls)
- No GPU required
- No large datasets (workspace < 10MB)
- Deterministic evaluation (seeded, pinned deps)
- Runnable without Docker (venv + local tools only)
- `setup.sh` replaces Dockerfile: installs system deps, creates files, seeds data

Categories: `software-engineering`, `debugging`, `data-science`, `devops`

Test files support pytest markers for scoring dimensions: `@pytest.mark.correctness`, `@pytest.mark.efficiency`

Shell checks in `tests/check.sh` return structured output (pass/fail per check with names)

#### Tier System

Tasks are assigned to tiers based on complexity and agent timeout budget:

| Tier | Tasks | Default agent timeout | Target wall time (4x parallel) |
|------|-------|-----------------------|-------------------------------|
| smoke | 8 | 120s | ~4 min |
| standard | 16 | 180s | ~12 min |
| full | 24 | 300s | ~30 min |

Tier config in `config/tiers.yaml`. Hourly runs use `smoke` or `standard`. `full` for nightly/weekly.

#### Curated Task List (24 tasks)

**Software Engineering (9)**

| Task ID | Source | Difficulty | Expert min | Tier | Notes |
|---------|--------|-----------|-----------|------|-------|
| fix-git | T-Bench port | easy | 5 | smoke | Recover lost git branches. Pure git, no deps. |
| new-encrypt-command | T-Bench port | easy | 5 | smoke | Implement encryption CLI. Clean coding task. |
| implement-from-tests | NEW | easy | 5 | smoke | Given only pytest files, write the module that makes them pass. TDD in reverse. |
| add-cli-subcommand | NEW | easy | 5 | standard | Given an existing argparse CLI, add a new subcommand with specific behavior. |
| git-multibranch | T-Bench port | medium | 10 | standard | Multi-branch merge resolution. Multi-step reasoning. |
| fix-circular-import | NEW | medium | 5 | standard | 5 Python modules with circular dependency. Restructure to fix it. |
| extract-class-refactor | NEW | medium | 8 | full | God-class with 400 lines. Extract subset into new class, update all callers. |
| multi-file-rename-refactor | NEW | medium | 8 | full | Rename an abstraction across 8 Python files. Coordinated edits. |
| api-migration | NEW | medium | 10 | full | Migrate REST endpoints v1->v2 across multiple modules. |

**Debugging (5)**

| Task ID | Source | Difficulty | Expert min | Tier | Notes |
|---------|--------|-----------|-----------|------|-------|
| fix-pandas-version | T-Bench port | easy | 5 | smoke | Version compatibility debugging (fix code, not swap installs). |
| fix-off-by-one | NEW | easy | 5 | smoke | Data processing script with subtle off-by-one errors across 3 functions. |
| fix-broken-serialization | NEW | medium | 5 | standard | JSON serialization roundtrip is broken. Diagnose from failing tests + error output. |
| debug-from-structured-logs | NEW | medium | 8 | full | Given app logs + stack traces, find and fix root cause. |
| makefile-fix | NEW | medium | 5 | full | Broken Makefile with dependency ordering issues. Fix so `make all` works. |

**Data Science / Scripting (6)**

| Task ID | Source | Difficulty | Expert min | Tier | Notes |
|---------|--------|-----------|-----------|------|-------|
| pandas-etl | T-Bench port | easy | 3 | smoke | CSV transformation pipeline. Quick, testable. |
| csv-to-parquet | T-Bench port | easy | 5 | smoke | Format conversion with schema handling. |
| heterogeneous-dates | T-Bench port | easy | 5 | smoke | Date format normalization (scripting/automation). |
| jq-data-processing | T-Bench port | easy | 5 | standard | JSON data transformation. |
| log-parser | NEW | medium | 5 | standard | Parse semi-structured logs into structured JSON. Hidden test inputs. |
| regex-extraction | NEW | medium | 5 | standard | Extract structured fields from messy text (emails, dates, IPs). Hidden test inputs. |

**Config / DevOps (4)**

| Task ID | Source | Difficulty | Expert min | Tier | Notes |
|---------|--------|-----------|-----------|------|-------|
| toml-yaml-migration | NEW | easy | 5 | standard | Convert a config system from TOML to YAML. Tests verify equivalent structure. |
| config-drift-detection | NEW | medium | 8 | full | Compare deployed config vs expected, generate drift report. |
| data-pipeline-validation | NEW | medium | 8 | full | Multi-step pipeline with schema validation and error handling. |
| dockerfile-to-shell | NEW | medium | 8 | full | Given a Dockerfile, produce equivalent setup.sh. Tests verify same environment state. |

#### Tier assignments

- **smoke (8)**: fix-git, new-encrypt-command, implement-from-tests, fix-pandas-version, fix-off-by-one, pandas-etl, csv-to-parquet, heterogeneous-dates
- **standard (16)**: smoke + add-cli-subcommand, git-multibranch, fix-circular-import, fix-broken-serialization, jq-data-processing, log-parser, regex-extraction, toml-yaml-migration
- **full (24)**: standard + extract-class-refactor, multi-file-rename-refactor, api-migration, debug-from-structured-logs, makefile-fix, config-drift-detection, data-pipeline-validation, dockerfile-to-shell

#### Backlog (revisit once harness is solid)

Tasks deferred due to heavy toolchains, slow runtimes, or grading complexity:
- **prove-plus-comm** (T-Bench) — requires Lean4/Coq theorem prover toolchain
- **conda-env-conflict** (T-Bench) — requires conda installed, solver is slow
- **nginx-request-logging** (T-Bench) — requires running nginx server, flaky without Docker
- **classifier-debug** (T-Bench) — ML training verification, grading ambiguity
- **ML/Research tasks** — deterministic fast grading for ML is an open design problem

#### Hidden Test Input Tasks (5+)

- **data-pipeline-validation**: workspace has example CSV; tests use held-out CSVs with edge cases in `tests/data/`
- **debug-from-structured-logs**: workspace has the buggy app; tests inject specific failure scenarios from `tests/data/`
- **config-drift-detection**: workspace has partial configs; tests check against full expected configs in `tests/data/`
- **log-parser**: workspace has example logs; tests parse held-out log samples from `tests/data/`
- **regex-extraction**: workspace has example text; tests extract from held-out messy text in `tests/data/`

#### Porting Guidelines

Each ported task from terminal-bench must be reviewed:
- Strip Docker dependency — `setup.sh` replaces Dockerfile
- Add proper seeding for determinism
- Add partial-credit test cases
- Use hidden test inputs in `tests/data/` where feasible
- Verify workspace < 10MB, no network/GPU requirements

#### New Task Design Guidelines

New tasks should stress-test capabilities terminal-bench misses:
- **Multi-file refactor**: coordinated changes across 5-10 files (extract-class-refactor, multi-file-rename-refactor, api-migration)
- **Debug from traces**: given logs/stack traces, diagnose root cause and fix (debug-from-structured-logs, fix-broken-serialization)
- **TDD / spec compliance**: implement code from tests or specs (implement-from-tests, add-cli-subcommand)
- **Config management**: infrastructure-as-code style tasks (config-drift-detection, toml-yaml-migration, dockerfile-to-shell)
- **Data extraction**: parse unstructured data into structured output (log-parser, regex-extraction)

### Success Criteria

- `tasks/` directory contains 24 task directories, each with valid task.yaml, tests/, and workspace/
- `uv run mhb tasks list` shows all tasks with category, difficulty, and tier
- `uv run pytest tasks/*/tests/ --collect-only` collects tests from all tasks without errors
- At least 5 tasks have hidden test inputs (test uses data not visible in workspace/)
- At least 16 tasks are new designs
- Reference solutions pass all tests for every task
- `uvx ruff check .` passes

### Verification

- `uv run pytest tests/ -v`
- `uvx ruff check .`
- `uv run mhb tasks list` shows 24 tasks
- Reference solution validation: `uv run mhb run --agent oracle --all` passes with correctness >= 0.95 on every task

---

## Spec 3: Reporting and Analysis

### Requirements

- `results/<run-id>/results.json` schema:
  ```json
  {
    "run_id": "string",
    "agent": "claude-code",
    "model": "claude-sonnet-4-20250514",
    "timestamp": "ISO8601",
    "config": {
      "tier": "smoke",
      "concurrency": 4,
      "default_agent_timeout_sec": 120
    },
    "tasks": {
      "<task-id>": {
        "correctness": 0.875,
        "tests_passed": 7,
        "tests_total": 8,
        "test_details": [{"name": "test_foo", "status": "passed", "marker": "correctness"}],
        "tokens": {"input": 12000, "output": 3400, "cache_read": 5000, "cache_write": 2000},
        "cost_usd": 0.045,
        "wall_time_sec": {"agent": 45.2, "test": 3.1, "total": 48.3},
        "timed_out": false,
        "max_agent_time_sec": 120,
        "failure_mode": null
      }
    },
    "summary": {
      "mean_correctness": 0.82,
      "total_cost_usd": 1.23,
      "total_tokens": 450000,
      "tasks_attempted": 12,
      "tasks_fully_solved": 9,
      "tasks_timed_out": 1,
      "total_wall_time_sec": 145.7
    }
  }
  ```
- `results/<run-id>/trajectories/<task-id>.jsonl`: one JSON object per line, each representing an agent turn/tool call with:
  - `timestamp`, `type` (tool_call | tool_result | assistant_message | user_message | system), `content`, `tokens` (if available)
- `uv run mhb results <run-id>` prints a rich CLI table: task id, correctness, tokens, cost, time, status, timed_out
- `uv run mhb compare <run-id-1> <run-id-2>` prints a side-by-side comparison table
- Model pricing config in `config/pricing.yaml` mapping model names to per-token costs (Anthropic + OpenAI models)

### Success Criteria

- results.json validates against the schema above
- trajectory JSONL files are parseable and contain >= 1 entry per task
- `mhb results` produces readable CLI output
- `mhb compare` shows delta between two runs
- `uv run pytest tests/ -v` passes
- `uvx ruff check .` passes

### Verification

- `uv run pytest tests/ -v`
- `uvx ruff check .`
- `uv run mhb results <run-id>` exits 0 with tabular output
- `uv run mhb compare <run-id-1> <run-id-2>` exits 0

---

## Hourly Run Profile

The primary use case: run after a hacking session to get fast feedback on agent quality.

| Tier | Tasks | Agent timeout | Worst-case serial | 4x parallel | Use case |
|------|-------|--------------|-------------------|-------------|----------|
| smoke | 8 | 120s | 16 min | ~4 min | Quick feedback after changes |
| standard | 16 | 180s | 48 min | ~12 min | Thorough hourly check |
| full | 24 | 300s | 120 min | ~30 min | Nightly / weekly |

Overhead per task: ~5-10s (worktree creation, venv copy, pytest execution). Warm venv cache eliminates install time.

Recommended hourly workflow:
```bash
# Quick smoke test
mhb run --agent tau --model claude-sonnet-4-6 --tier smoke --concurrency 4

# After bigger changes, run standard
mhb run --agent tau --model claude-sonnet-4-6 --tier standard --concurrency 4

# Full suite nightly
mhb run --agent tau --model claude-sonnet-4-6 --tier full --concurrency 4
```

---

## Architecture

```
mini-harness-bench/
  pyproject.toml
  README.md
  config/
    pricing.yaml              # model token pricing (Anthropic + OpenAI)
    tiers.yaml                # tier definitions (tasks, timeouts)
  mhb/                        # main package
    cli.py                    # argparse CLI entry point
    harness.py                # orchestrator: task setup, agent run, test, score
    scoring.py                # multi-dimensional scoring logic
    agents/
      base.py                 # abstract agent interface
      claude_code.py          # Claude Code adapter (stream-json parsing)
      codex.py                # Codex adapter
      tau.py                  # Tau adapter (trace-output + stats-json parsing)
      oracle.py               # runs reference solution
    tasks/
      loader.py               # load task.yaml, discover tasks, tier filtering
      workspace.py            # git worktree + venv setup/teardown + caching
    evaluation/
      runner.py               # pytest + shell check execution
      parser.py               # parse pytest output + shell check output into scores
    reporting/
      results.py              # results.json writer
      trajectory.py           # JSONL trajectory logger
      display.py              # rich CLI tables
      compare.py              # run comparison
  tasks/                      # task definitions (each is a subdirectory)
    <task-id>/
      task.yaml
      setup.sh
      workspace/
      tests/
      tests/data/             # hidden test inputs (not copied to agent worktree)
      reference/
  tests/                      # harness unit tests
  results/                    # output directory (gitignored)
```

## Key Design Decisions

1. **No Docker for v1**: tasks run in git worktrees with uv venvs. Faster iteration, easier debugging. `setup.sh` replaces Dockerfile.
2. **Native agent tooling**: each agent uses its own CLI as intended (Claude stream-json, Codex exec, Tau --trace-output). We capture their output rather than constraining them to a uniform interface.
3. **Git worktrees as audit trail**: every agent action is visible in git history. Log all commands/tool calls to JSONL and inspect the worktree diff post-hoc.
4. **Partial credit via pytest**: score = passed/total. Pytest markers (`@correctness`, `@efficiency`) allow dimensional breakdown.
5. **Token tracking from agent output**: Claude Code's stream-json, Tau's run.json/stats-json, and Codex's output all include token counts. Parse them from trajectory.
6. **Hidden test inputs where feasible**: tasks provide example data in workspace/, but evaluation tests use held-out inputs in tests/data/ the agent never sees. Prevents hardcoding.
7. **Tiered execution for speed**: smoke/standard/full tiers with escalating timeouts and task counts. Enables hourly runs with the smoke tier.
8. **Parallel by default**: tasks are isolated in their own worktrees + venvs, so 4x concurrency is safe and cuts wall time by 4x.
9. **Venv caching**: warm starts via `~/.cache/mhb/venvs/` eliminate repeated pip installs across runs.
10. **Hard timeout enforcement**: kill agent process on timeout, score partial credit. Prevents runaway tasks from blocking the suite.

## Non-Goals for v1

- No web dashboard or leaderboard
- No Supabase/database integration
- No asciinema recording
- No Docker/container isolation
- No MCP integration
- No ML/research tasks (deferred — grading design is complex for fast benchmarks)
- No incremental run modes (`--changed`, `--failed`) — focus on making the full suite fast instead

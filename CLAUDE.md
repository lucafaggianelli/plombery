# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Plombery is a Python task scheduler with a built-in web UI and REST API. Users define **Pipelines** (collections of **Tasks**) in pure Python, attach APScheduler-based **Triggers** for scheduling, and Plombery runs them, stores results, and streams real-time logs via WebSocket.

Stack: FastAPI + APScheduler + SQLAlchemy (SQLite default) + Socket.IO on the backend; React + TypeScript + Vite + Tailwind + Tremor on the frontend.

## Commands

### Backend (Python)

```sh
# Install with dev dependencies
uv sync --dev

# Run all tests
pytest

# Run a single test file or test
pytest tests/test_api.py
pytest tests/test_api.py::test_api_list_pipelines

# Run with coverage
coverage run -m pytest
coverage report -m

# Lint / format
flake8
black .
```

Tests automatically use an in-memory SQLite database (`DATABASE_URL=sqlite:///:memory:`) — no setup needed.

### Frontend (React/TypeScript)

The frontend uses **pnpm** as the package manager.

```sh
cd frontend/

# Install dependencies
pnpm install   # or just: pnpm

# Development server (hot-reload, proxies API to localhost:8000)
pnpm dev

# Production build (outputs to frontend/dist/, embedded into the Python package)
pnpm build
```

### Running the Example App

```sh
cd examples/
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run.sh     # or ./run.ps1 on Windows
```

The example app runs with `--reload` pointing at the parent directory, so changes to the `plombery` package are picked up live.

### The `plombery` CLI

`plombery run` (`cli.py`, a `click` group, entry point in `pyproject.toml`) imports a `pipelines` module/package — a `pipelines/` folder, importing every submodule so each `register_pipeline` runs — then serves the app with uvicorn. It's the no-`app.py` way to start; `app.py` + `get_app()` still works. Single process for now; the `serve`/`worker` split waits for the scheduler rework.

### Documentation

```sh
mkdocs serve
```

## Architecture

### Core Python Package (`src/plombery/`)

The main entry point is `src/plombery/__init__.py`, which exposes `register_pipeline`, `get_app`, `task`, `Task`, `Pipeline`, `Trigger`, `BaseSecrets`, `OutputOf`, `MappingMode`, and `PipelineRunStatus`.

**Execution flow (DAG, event-driven):**
1. A pipeline is a graph of tasks, built with the `Pipeline` context manager (tasks defined inside are auto-added; `>>`/`<<` declare edges) or the flat `register_pipeline(id=..., tasks=[...])` form. `register_pipeline` accepts either a built `Pipeline` or the flat arguments.
2. Edges live on `Pipeline` (`_upstream`/`_downstream`, keyed by task id — see `Pipeline.add_edge`/`upstream_of`/`downstream_of`), never mutated onto `Task` objects, so the same `Task` can be wired into more than one pipeline without one leaking into the other's scheduling decisions.
3. `_Orchestrator` (`orchestrator/__init__.py`) schedules a trigger's `run()` via APScheduler. `run()` (`orchestrator/executor.py`) starts the tasks with no upstream dependencies (`start_pipeline_tasks`); each task instance executes independently and calls `handle_task_completion` when done, which schedules whatever becomes ready — fan-out/fan-in, `OutputOf` bindings and `fail_fast` are all resolved there.
4. Task output is stored in the database (`TaskRunOutput`), not on disk. Logs are streamed to disk (JSONL) and over Socket.IO.
5. Python `contextvars` (`pipeline_context`, `task_context`, `run_context`, `task_run_context` in `pipeline/context.py`) carry pipeline/run state into task functions and the logger.

**Key modules:**
- `pipeline/pipeline.py` — `Pipeline`: the DAG's edges, `OutputOf` cross-validation, versioning (`get_version()`)
- `pipeline/tasks.py` — `Task`, `@task`, `OutputOf`/`OutputOfMarker`, `>>`/`<<`
- `pipeline/trigger.py` — `Trigger` (schedule, params, pause state)
- `secrets.py` — `BaseSecrets`, a `pydantic_settings.BaseSettings` subclass for typed secret schemas
- `orchestrator/__init__.py` — the DAG scheduler: `_Orchestrator`, `handle_task_completion`, `run_pipeline_now()`
- `orchestrator/executor.py` — `run()`/`execute_task_instance`/`_execute_task`: resolves a task's arguments (by name or `OutputOf`) and calls it
- `orchestrator/dag.py` — `is_graph_acyclic(task_ids, upstream_of)`, a pure function over a plain adjacency mapping
- `database/` — SQLAlchemy models (`PipelineRun`, `TaskRun`, `TaskRunOutput`), Alembic migrations, repository functions; `SessionLocal` is a context-manager session factory
- `api/__init__.py` — FastAPI app wiring: mounts Socket.IO at `/ws`, adds routers under `/api`, serves SPA from root
- `api/routers/pipelines.py` — REST endpoints: list/get pipelines, get input schema, trigger manual run
- `api/authentication.py` — OAuth2 via Authlib; `NeedsAuth = Depends(_needs_auth)` is used on all API routers; auth is entirely optional (controlled by `settings.auth`)
- `logger/__init__.py` — `get_logger()` returns a per-run `LoggerAdapter` that writes JSONL to disk and streams via Socket.IO
- `notifications/__init__.py` — `NotificationManager` uses Apprise to send alerts based on `NotificationRule` objects

**Configuration** (`config/model.py`): loaded via `pydantic-settings` from env vars, `.env` file, and a YAML settings file. Key settings: `database_url`, `data_path`, `auth`, `notifications`, `allowed_origins`, `frontend_url`. This is Plombery's own system configuration — unrelated to `BaseSecrets`, which is for the secrets a *pipeline* needs.

## Documentation

The `docs/` site is user-facing reference material, published with MkDocs. When touching anything that changes a documented behavior — the public API in `plombery/__init__.py`, a pipeline/task/trigger/secrets pattern, a CLI or config option — update the relevant page(s) under `docs/` in the same change. Docs that fall behind the code are worse than no docs.

Rules for writing it:

- **Write for the end user, not for the project's history.** Explain how to do something today. Never narrate what changed, why a design was chosen over another, or reference past versions/decisions — that belongs in `CHANGELOG.md` and commit messages, not in reference docs.
- **Be complete.** If something can be done in more than one valid way (e.g. the `Pipeline` context manager vs. the flat `register_pipeline(id=..., tasks=[...])` form), document all of them, not just the recommended one, and say when to prefer which.
- **Every code example must actually run.** Missing imports, undecorated functions passed where a `Task` is required, a required field silently omitted (e.g. `Trigger.name`) — these are bugs. When in doubt, paste the example into a scratch file and run it against the installed package before trusting it.
- **Secrets get their own page** (`docs/secrets.md`), not a subsection buried in `tasks.md` — they're looked up on their own, independently of whatever else someone is reading.
- **Formal tone, no filler.** State the behavior directly; skip meta-commentary about the documentation itself.

The living roadmap for where the project is headed is `ROADMAP.md` at the repo root — keep it current when a phase's status changes, and keep it in the same plain, undecorated style (no AI-generated meta-commentary, no restating of the obvious).

### Frontend (`frontend/src/`)

File-system based routing: `frontend/src/Router.tsx` uses `import.meta.glob` to auto-discover all `pages/**/*.tsx` files and maps `[param]` folder segments to `:param` route params.

Pages follow the hierarchy: `/` → pipeline list; `/pipelines/:pipelineId` → pipeline detail with trigger list; `/pipelines/:pipelineId/triggers/:triggerId` → trigger detail with runs list; `/pipelines/:pipelineId/triggers/:triggerId/runs/:runId` → run detail with logs and task output.

Real-time updates arrive via `socket.io-client` (`contexts/WebSocketContext.tsx`) on the `run-update` event. Data fetching uses `@tanstack/react-query`. Forms for pipeline input params are auto-generated from the JSON Schema returned by `GET /api/pipelines/:id/input-schema` (`components/JsonSchemaForm.tsx`).

### Pipeline Definition Pattern

Users write pipelines using the public API — the `Pipeline` context manager (recommended: tasks defined inside are auto-added, and the pipeline registers itself when the block ends) or the flat `register_pipeline(id=..., tasks=[...])` form. `plombery run` (`cli.py`) discovers and imports the `pipelines/` package so each one registers; a hand-written `app.py` + `get_app()` still works.

```python
from apscheduler.triggers.interval import IntervalTrigger
from plombery import task, Pipeline, Trigger

with Pipeline(
    id="my_pipeline",
    triggers=[Trigger(id="every_hour", name="Every hour", schedule=IntervalTrigger(hours=1))],
) as pipeline:
    @task
    async def fetch():
        return {"result": 42}

    @task
    def process(fetch):  # resolved by name: an upstream task id
        return fetch["result"] + 1

    fetch >> process
# registered here, when the block ends (auto_register=False opts out)
```

`register_pipeline` remains for the flat form and for a pipeline built with `auto_register=False`. `Pipeline.__exit__` registers via `orchestrator.register_pipeline`, which is idempotent for the same object.

A task's arguments are resolved by name against upstream task ids declared with `>>`/`<<` (never by position — the DAG isn't a sequence), or explicitly with `OutputOf(task)` when the argument shouldn't have to be named after it. `>>`/`<<` is the only thing that declares an edge; `OutputOf` only binds data, and `Pipeline` rejects the two disagreeing. Everything a task receives is dependency-injected by matching its signature (`orchestrator/executor.py:check_task_signature`): `params` (the pipeline's Pydantic params model), `context`/`ctx` (the `Context`), an argument annotated with a `BaseSecrets` subclass (an injected, validated secrets instance — matched by annotation, so it can have any name), and everything else as upstream task output. Any of them can be omitted. Because secrets are declared in the signature, `check_registered_pipelines()` (called once at startup) records on each `Pipeline` the problems that keep it from running — a missing secret, scoped to the task that needs it — as `pipeline.issues` (a list of `PipelineIssue`), with `pipeline.runnable` computed from them. The API serves the stored `issues`/`runnable`; they are not recomputed per request.

`Pipeline(fail_fast=False)` keeps a fan-out's healthy branches running to completion when one branch fails, instead of cancelling everything downstream of the branches still in flight.

### Database Migrations

Alembic is configured in `src/plombery/alembic/`. When `setup_database()` is called on startup, it applies any pending migrations automatically. New migrations go in `src/plombery/alembic/versions/`.

### Frontend Build Integration

`pnpm build` outputs to `frontend/dist/`. The `SPAStaticFiles` middleware in `api/middlewares.py` serves these static files and falls back to `index.html` for client-side routing. The built assets are included in the Python package via `MANIFEST.in`.

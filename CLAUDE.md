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

### Documentation

```sh
mkdocs serve
```

## Architecture

### Core Python Package (`src/plombery/`)

The main entry point is `src/plombery/__init__.py`, which exposes `register_pipeline`, `get_app`, `task`, `Task`, `Pipeline`, `Trigger`, and `PipelineRunStatus`.

**Execution flow:**
1. User calls `register_pipeline(...)` → stored in `orchestrator._all_pipelines`
2. `_Orchestrator` (APScheduler `AsyncIOScheduler`) schedules jobs for each non-paused `Trigger`
3. When a trigger fires (or a manual run is requested via API), `executor.run()` is called
4. `executor.run()` iterates over `pipeline.tasks`, calls each task function, stores output as JSON in `.data/runs/run_<id>/`, and emits `run-update` WebSocket events
5. Python `contextvars` (`pipeline_context`, `task_context`, `run_context` in `pipeline/context.py`) carry pipeline/run state into task functions and the logger

**Key modules:**
- `pipeline/pipeline.py`, `pipeline/task.py`, `pipeline/trigger.py` — Pydantic models for user-facing API
- `orchestrator/__init__.py` — wraps APScheduler, holds pipeline registry, exposes `run_pipeline_now()`
- `orchestrator/executor.py` — async `run()` function that executes pipelines task-by-task
- `orchestrator/data_storage.py` — reads/writes task output JSON and run log files under `.data/`
- `api/__init__.py` — FastAPI app wiring: mounts Socket.IO at `/ws`, adds routers under `/api`, serves SPA from root
- `api/routers/pipelines.py` — REST endpoints: list/get pipelines, get input schema, trigger manual run
- `api/authentication.py` — OAuth2 via Authlib; `NeedsAuth = Depends(_needs_auth)` is used on all API routers; auth is entirely optional (controlled by `settings.auth`)
- `logger/__init__.py` — `get_logger()` returns a per-run `LoggerAdapter` that writes JSONL to disk and streams via Socket.IO
- `notifications/__init__.py` — `NotificationManager` uses Apprise to send alerts based on `NotificationRule` objects
- `database/` — SQLAlchemy models (`PipelineRun`), Alembic migrations, and repository functions; `SessionLocal` is a context-manager session factory

**Configuration** (`config/model.py`): loaded via `pydantic-settings` from env vars, `.env` file, and a YAML settings file. Key settings: `database_url`, `data_path`, `auth`, `notifications`, `allowed_origins`, `frontend_url`.

### Frontend (`frontend/src/`)

File-system based routing: `frontend/src/Router.tsx` uses `import.meta.glob` to auto-discover all `pages/**/*.tsx` files and maps `[param]` folder segments to `:param` route params.

Pages follow the hierarchy: `/` → pipeline list; `/pipelines/:pipelineId` → pipeline detail with trigger list; `/pipelines/:pipelineId/triggers/:triggerId` → trigger detail with runs list; `/pipelines/:pipelineId/triggers/:triggerId/runs/:runId` → run detail with logs and task output.

Real-time updates arrive via `socket.io-client` (`contexts/WebSocketContext.tsx`) on the `run-update` event. Data fetching uses `@tanstack/react-query`. Forms for pipeline input params are auto-generated from the JSON Schema returned by `GET /api/pipelines/:id/input-schema` (`components/JsonSchemaForm.tsx`).

### Pipeline Definition Pattern

Users write pipelines using the public API:

```python
from plombery import get_app, register_pipeline, task, Task, Trigger
from apscheduler.triggers.interval import IntervalTrigger

@task
async def my_task(params):
    return {"result": 42}

register_pipeline(
    id="my_pipeline",
    tasks=[my_task],
    triggers=[Trigger(id="every_hour", name="Every hour", schedule=IntervalTrigger(hours=1))],
)

app = get_app()  # pass to uvicorn
```

Tasks receive the previous task's return value as the first positional argument (data flowing), and the pipeline's Pydantic params model via a `params` keyword argument. Either or both can be omitted.

### Database Migrations

Alembic is configured in `src/plombery/alembic/`. When `setup_database()` is called on startup, it applies any pending migrations automatically. New migrations go in `src/plombery/alembic/versions/`.

### Frontend Build Integration

`pnpm build` outputs to `frontend/dist/`. The `SPAStaticFiles` middleware in `api/middlewares.py` serves these static files and falls back to `index.html` for client-side routing. The built assets are included in the Python package via `MANIFEST.in`.

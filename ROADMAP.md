# Roadmap

Where Plombery is headed, in order. Each phase is meant to ship and be useful
on its own — nothing here is blocked on a phase after it.

## Phase 0 — DAG execution — done

- Pipelines are a graph of tasks, not a sequence: `>>`/`<<` declare
  dependencies, fan-out/fan-in via `MappingMode`.
- `Pipeline(fail_fast=False)` keeps the healthy branches of a fan-out running
  when one branch fails.
- Retention policy for run history and log files.
- Pipeline versioning (`Pipeline.get_version()`), recorded on every run.
- `register_pipeline` accepts a `Pipeline` built with the context manager, not
  only the flat `id`/`tasks`/... form.
- A task can be defined outside a `with Pipeline()` block and only wired
  inside it.
- `OutputOf(task)` binds a task argument to a specific upstream task's
  output, so the argument doesn't have to be named after it. A mismatch
  between an `OutputOf` binding and the declared `>>`/`<<` dependency is a
  validation error.
- `Task` is safe to reuse across pipelines: dependency edges live on
  `Pipeline`, not on `Task`.
- `BaseSecrets`: typed secret declarations, resolved from environment
  variables or a `.env` file, no YAML or code generation involved.

## Phase 1 — Own scheduler

APScheduler is the last piece standing between Plombery and running well on
serverless/scale-to-zero infrastructure, and its job store has no persistence
across restarts.

- Replace APScheduler with a DB-backed scheduler: schedules and next-fire
  times persist across restarts.
- Task execution model: a dedicated thread per task by default (not
  `asyncio.to_thread`, whose pool blocks process shutdown), with an opt-in
  process-isolated tier for tasks that need real cancellation or resource
  limits.
- Async SQLAlchemy on the request/scheduler path; task code keeps using the
  sync API.
- `serve` and `worker` as separate processes, with `plombery run` supervising
  both for the single-process case.
- Runtime observability: worker heartbeat, stuck/zombie run detection,
  `/api/health`.
- Raise the minimum Python version once the above lands.

## Phase 2 — Blocks and connections

- A block registry: reusable, configurable units (HTTP request, run SQL,
  read/write with polars) usable as plain `@task`-compatible functions ahead
  of any visual editor.
- `Connection`: a named, typed resource (a database, a bucket) that a block
  can request without knowing how it's backed. Declared as a Python object,
  like `BaseSecrets`.
- `plombery init`: project scaffolding via the CLI.

## Phase 3 — Visual editor

- A canvas to build and edit pipelines visually, backed by the block
  registry from Phase 2.
- System configuration editable from the UI where it's safe to hot-reload,
  clearly marked where it isn't.

## Phase 4 — Event triggers

- Triggers beyond schedules and manual runs: file watchers, webhooks,
  upstream dataset changes, cross-pipeline dependencies.

## Phase 5 — Sandboxed code blocks

- Resource limits and an opt-in sandbox for user-supplied code blocks in the
  visual editor, building on the process-isolated execution tier from
  Phase 1.

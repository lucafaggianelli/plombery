# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added

- Support for DAGs and Fan-out / Dynamic Mapping tasks ([#529](https://github.com/lucafaggianelli/plombery/issues/529))
- Add `context` arg to tasks
- Show pipeline tasks as an interactive graph
- Deployment documentation
- Retention policy for runs data, with independent thresholds for log
  files and for run history (`retention.files_days`, `retention.runs_days`)
- Record on every run the version of the pipeline it executed, either the
  `version` set on the pipeline or a hash of its task graph
- Warn when a task blocks the event loop, naming it, since that freezes the
  API and the live logs (`blocked_loop_threshold`)
- `Pipeline(fail_fast=False)` keeps the healthy branches of a fan-out running
  when one of them fails, for pipelines whose branches are independent of each
  other, such as one per input file
- `register_pipeline` also accepts a `Pipeline` built with the `with Pipeline()`
  context manager, not only the flat `id`/`tasks`/... form
- `OutputOf(task)` binds a task argument to a specific upstream task's output,
  so the argument doesn't have to be named after it. A type checker still
  verifies the argument's declared type against what `task` actually returns.
  It only binds data: the dependency itself still has to be declared with
  `>>`/`<<`, and a mismatch between the two is now a validation error
- `BaseSecrets`, a typed way to declare the secrets a pipeline needs: subclass
  it with the fields a task requires, and it resolves them from an
  environment variable of the same name, or from a `.env` file — no YAML, no
  code generation, the class itself is the declaration

### Fixed

- A task downstream of a fan-out now receives the output of every mapped
  instance, instead of `None`
- An orchestration error, such as a fan-out over a non collection, now fails the
  run instead of leaving it running forever
- A task argument with a default value is no longer overwritten with `None` when
  it doesn't name an upstream task
- Tasks annotated with generic types, such as `List[int]`, no longer fail
- Close the log file descriptors of every task and mapped instance, not only the
  ones of the pipeline logger
- A run no longer hangs in `running` forever when two mapped branches are
  skipped at once, when the pipeline has no tasks, or when the input params
  fail validation
- Every `run-update` websocket event now carries the run, so the runs list
  stops showing a finished run as still going
- Live log lines are no longer labelled with the wrong task when several
  tasks run at the same time, and are streamed on the server event loop
  instead of a new one per line
- A fan-in task is scheduled once instead of once per branch when several
  branches finish while a websocket client is connected
- A task returning a `pandas.DataFrame` is stored instead of failing the run
- When a fan-out branch fails, the tasks below the branches that were still
  running are recorded as cancelled rather than silently left out of the run
- Wiring the same `Task` object into two different pipelines no longer makes
  one pipeline's dependencies leak into the other's scheduling decisions
- A task defined outside a `with Pipeline()` block now joins the pipeline when
  wired with `>>` inside it, instead of being silently left out

### Changed

- (breaking) Task dependencies must be defined explicitly

## [0.5.2] - 2025-11-30

### Added

- Add libsql database support ([#525](https://github.com/lucafaggianelli/plombery/issues/525))

### Fixed

- Fix Select field in pipeline run dialog ([#537](https://github.com/lucafaggianelli/plombery/issues/537))

## [0.5.1] - 2025-10-28

### Fixed

- alembic.ini file was not correctly packaged

## [0.5.0] - 2025-10-28

### Added

- Database migrations managed by Alembic (#142)
- Pre-defined auth providers for Google and Microsoft
- Config for data directory (close #299)
- Link to REST API docs in settings menu
- Add download task data button in data view dialog (close #46)
- Add support to Pydantic's `SecretStr` input types (by @flashdagger)

### Fixed

- Release logger resources after run (fix #491)
- Improve task data visualization (#257)
- Check data file paths before accessing them
- Fixed boolean parameter input when default is True (by @flashdagger)
- Fix connection with non sqlite db (#392) (by @PierrickBrun)

### Changed

- Migrated plain websocket to SocketIO for improved communication stability
- (internal): pipeline HTTP run url is now `/pipelines/{pipeline_id}/run`
- (internal): updated frontend dependencies

### Removed

- Removed python `websockets` dependency

## [0.4.1] - 2023-10-11

### Fixed

- No pipelines message appearing when pipelines where there
- Fix the traceback info dialog (fix #229)

## [0.4.0] - 2023-10-06

### Added

- Navigate to run page after running manually a pipeline or trigger (#71)
- Add `ky` frontend dependency as HTTP fetch library
- Spin the running icon in the status badge
- Add a live logs indicator to the logs viewer
- Add duration timer to run page
- Automatic scroll lock for the log stream
- Show UTC datetime when hovering a datetime
- Implement Dark mode and theme switcher
- Create a settings menu (#157)
- (docs): added recipe SSL certificate check
- (docs): document pipelines and tasks (#110)
- Improve manual run form
- (docs): add codespaces config to run demo
- Add `allowed_origins` configuration to explicitly set CORS headers
- Add HTML template for email notifications (#52)
- Add in-app messages for new users to get started (#38)
- Use skeleton loaders during data fetch

### Fixed

- Sometimes logs are appended to an existing logs files of previous runs (#131)
- During a pipeline run, logs are streamed to any pipeline run page bug (#130)
- Check task function signature before calling it (#154)
- Fix link arrow decoration in scrolling containers
- Fix table sticky headers
- Show absolute URL in trigger run hook (#82)
- Re-implement dialog to fix several bugs (#81)
- Validate parameters in pipeline run endpoint
- Derive correct WebSocket scheme from the HTTP URL scheme
- Fix context in sync tasks functions (#153)
- Show validation errors in manual run form dialog (#192)

### Changed

- Migrate tremor to v3
- Update frontend deps
- (breaking) updated FastAPI to v0.103 (#144)
- updated authlib for compatibility with fastapi
- (internal): refactored FastAPI backend (#159)
- (breaking): auth redirect url is now `/auth/redirect`
- (breaking): all auth endpoints are prefixed with `/auth`
- (breaking): `pipelines/`, `runs/` and `ws/` endpoints now have trailing slashes
- (breaking): updated pydantic to v2
- (breaking): `Trigger.params` accepts a `BaseModel` instance, not a dict
- (breaking): By default CORS headers allow_origins is set to `*`

### Removed

- Remove `server_url` configuration as unused

## [0.3.2] - 2023-06-20

### Added

- Add next fire time to pipelines and triggers (#27)
- show run time in runs list (#129)

### Changed

- Save times with UTC timezone (#132)

### Fixed

- change taskrun duration from positive to non-negative (#128)
- specify button type when in form to avoid submit (#133)
- Fix the run pipeline dialog open/close logic
- Show pipeline name in runs list (#127)

[Unreleased]: https://github.com/lucafaggianelli/plombery/compare/0.4.1...HEAD
[0.4.1]: https://github.com/lucafaggianelli/plombery/compare/0.4.0...0.4.1
[0.4.0]: https://github.com/lucafaggianelli/plombery/compare/0.3.2...0.4.0
[0.3.2]: https://github.com/lucafaggianelli/plombery.git/releases/tag/0.3.2

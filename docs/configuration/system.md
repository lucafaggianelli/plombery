---
icon: material/wrench
---

!!! tip

    If you're running Plombery locally, in most cases you don't need to change
    these settings

## `allowed_origins`

**Change it if running in production.**

It allows to configure the CORS header `Access-Control-Allow-Origin`,
by default it's value is `*` so it allows all origins.

## `data_path`

The absolute path to the data directory where logs and output data is stored.

By default is set to the current working directory.

## `database_url`

The DB URI, by default `sqlite:///./plombery.db`

## `database_auth_token`

The auth token for libsql databases hosted on Turso cloud

## `blocked_loop_threshold`

Plombery runs a task declared with `async def` on the event loop, and a task
declared with `def` in a thread. A coroutine that calls blocking code — a plain
`time.sleep`, a synchronous HTTP client, a long CPU loop — holds the loop for
its whole duration, and while it does **nothing else in the process runs**: the
API stops answering, the live logs stop streaming and the scheduler stops
firing. The symptom is a frozen UI with nothing in the logs to explain it.

Plombery watches for this and logs a warning naming the tasks that were running:

```
The event loop was blocked for 12.4s while these tasks were running:
fetch_report. An async task must not call blocking code: use await, or declare
the task with `def` instead of `async def` so that Plombery runs it in a thread.
```

The threshold is 2 seconds by default. Set it to `0` to turn the check off.

```yaml title="plombery.config.yaml"
blocked_loop_threshold: 2
```

!!! tip

    The fix is almost always one of two things: `await` the blocking call if an
    async version exists, or drop the `async` from the task definition, so that
    Plombery runs it in a thread where blocking is harmless.

## `retention`

By default Plombery keeps every run forever. Set one or both thresholds to
reclaim space automatically; the policy is applied at startup and then once a
day.

```yaml title="plombery.config.yaml"
retention:
  # delete the log files of runs that finished more than 30 days ago,
  # keeping the runs themselves so the history and the charts are intact
  files_days: 30
  # delete the runs that finished more than a year ago, with their task
  # runs, their stored outputs and their log files
  runs_days: 365
```

Both are optional and independent: setting only `files_days` keeps the whole
history while dropping the logs, setting only `runs_days` deletes old runs
entirely.

!!! note

    Task outputs are stored in the database, not on disk, so `runs_days` is the
    threshold that reclaims most of the space. `files_days` only affects log
    files.

Runs that haven't finished are never deleted, however old they are, and data
directories left behind by runs that are no longer in the database are cleaned
up as well.

## `frontend_url`

The URL of the frontend, by default is the same as the backend,
change it if the frontend is served at a different URL, for example
during the frontend development.

## `pipeline_version`

The [version](../pipelines.md#versioning) recorded on every run, for the
pipelines that don't declare a `version` of their own.

Set it to the revision the deployment was built from — as an environment
variable, `PIPELINE_VERSION=$(git describe --tags --always)` — since an image
ships without the git history Plombery would otherwise read the version from.

When it's unset and there is no repository either, runs record no version.

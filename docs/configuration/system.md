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

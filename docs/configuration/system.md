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

## `frontend_url`

The URL of the frontend, by default is the same as the backend,
change it if the frontend is served at a different URL, for example
during the frontend development.

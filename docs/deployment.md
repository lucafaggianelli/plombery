---
icon: material/rocket-launch
---

Plombery is designed to run as **a single process on a single machine**: one
`uvicorn` process serves the REST API, the web UI and runs the scheduler and
your pipelines. There is no broker, no worker pool and no separate scheduler
service to operate.

## Running in production

Your app is an ASGI application, so any ASGI server will do. Assuming your app
lives in `app.py`:

```py title="app.py"
from plombery import get_app

# import the modules that register your pipelines
import my_pipelines  # noqa

app = get_app()
```

Run it with:

```sh
uvicorn app:app --host 0.0.0.0 --port 8000
```

!!! danger "Do not run multiple workers"

    Don't use `--workers N`, and don't run several instances against the same
    database. The scheduler lives inside the process and its state is in memory,
    so every worker keeps its own copy of the schedule and every scheduled run
    would be fired **once per worker**.

    If you need to survive a restart of the machine, use a process supervisor
    that runs a single instance, such as systemd or your container platform's
    restart policy.

## What has to be persisted

Two things outlive a run and must be on durable storage:

| What | Where | Setting |
| --- | --- | --- |
| Run history | The database, `./plombery.db` by default | `database_url` |
| Logs and task output | The `.data/` directory, under the working directory by default | `data_path` |

If either is on an ephemeral filesystem, you lose the run history and the logs
at every restart. See [Database](configuration/database.md) for using something
other than SQLite, and [System](configuration/system.md) for `data_path`.

## Behind a reverse proxy

When Plombery is served on a domain rather than on `localhost:8000`, set the
public URL and restrict CORS:

```yaml title="plombery.config.yaml"
frontend_url: https://plombery.example.com
allowed_origins:
  - https://plombery.example.com
```

A minimal nginx site, remembering that the UI uses WebSockets for live logs:

```nginx
server {
    server_name plombery.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # required for the live logs
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# keep the database and the run data on a volume
ENV DATABASE_URL=sqlite:////data/plombery.db
ENV DATA_PATH=/data
VOLUME /data

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## systemd

```ini title="/etc/systemd/system/plombery.service"
[Unit]
Description=Plombery
After=network.target

[Service]
Type=simple
User=plombery
WorkingDirectory=/opt/plombery
ExecStart=/opt/plombery/.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Before you expose it

Plombery runs the Python code you gave it, and the UI can trigger any pipeline.
Anyone who can reach it can run your pipelines and read their output, so on a
public address you should always
[enable authentication](configuration/auth/generic-oauth.md), and set
`auth.secret_key` to a real secret rather than leaving the default.

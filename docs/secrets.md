---
status: new
---

# Secrets

A secret is a credential a task needs at runtime — a database password, an API
key, a token. Plombery doesn't have a secret store of its own: a secret is
declared as a typed schema in Python, and its value is resolved from an
environment variable or a `.env` file.

## Declaring a secret

Subclass `BaseSecrets`, the same way a pipeline's input parameters are a plain
[Pydantic](https://docs.pydantic.dev/latest/usage/models/) model:

```py
from pydantic import SecretStr
from plombery import BaseSecrets


class WarehouseSecrets(BaseSecrets):
    WAREHOUSE_URI: SecretStr
```

Declaring a field as `SecretStr` keeps its value out of `repr()` and out of
the logs — printing or logging the object shows `**********` instead of the
real value. It isn't required: a field can be a plain `str`, `int`, or any
other type a secret-shaped value needs to be (an API key that a client
library requires as a plain `str`, for instance).

## Using a secret in a task

Declare the secrets a task needs as an argument annotated with the class, and
Plombery injects a validated instance when the task runs — the same way it
injects `params` and the `context`:

```py
from plombery import task

from .secrets import WarehouseSecrets


@task
def load_to_warehouse(rows, secrets: WarehouseSecrets):
    engine = create_engine(secrets.WAREHOUSE_URI.get_secret_value())
    ...
```

The argument is matched by its annotation, not its name, so it can be called
anything. It's kept separate from the arguments that carry upstream task
output, so it's never confused with one.

Declaring the secret as an argument, rather than constructing the class inside
the task body, is what lets Plombery know at startup which secrets each
pipeline needs — see [Checking secrets at startup](#checking-secrets-at-startup)
— and lets the task be called with a stand-in in tests.

## Where values come from

A field's value is read, in order:

1. From an environment variable of the same name, case insensitive. `WAREHOUSE_URI` above reads the `WAREHOUSE_URI` environment variable.
2. From a `.env` file in the current working directory, if the environment variable isn't set.

```sh title=".env"
WAREHOUSE_URI=postgres://user:password@host:5432/warehouse
```

A field with no default value is required: constructing the class without a
value available raises a `pydantic.ValidationError` immediately, naming the
missing field. This is deliberate — a missing secret should fail loudly where
it's declared, not resolve to `None` and fail later wherever a task happens to
use it.

A field can declare a default, making it optional:

```py
class WarehouseSecrets(BaseSecrets):
    WAREHOUSE_URI: SecretStr
    WAREHOUSE_SCHEMA: str = "public"
```

## Several secrets, several classes

Group secrets by the external system they belong to — one class per database,
API or bucket — not all in one class, and not per pipeline. The same
credential is often shared by several pipelines, so a per-system class is
declared once and reused, and a task ends up requiring only the secrets it
actually uses:

```py title="secrets.py"
from pydantic import SecretStr
from plombery import BaseSecrets


class WarehouseSecrets(BaseSecrets):
    WAREHOUSE_URI: SecretStr


class WeatherApiSecrets(BaseSecrets):
    WEATHER_API_KEY: SecretStr
```

```py title=".env"
WAREHOUSE_URI=postgres://user:password@host:5432/warehouse
WEATHER_API_KEY=a1b2c3d4
```

A task that declares only `WeatherApiSecrets` doesn't require `WAREHOUSE_URI`
to be set, and vice versa: a missing secret only affects the pipelines whose
tasks declare it.

## Checking secrets at startup

Because a task declares the secrets it needs as arguments, Plombery knows,
when it starts, exactly which secrets every registered pipeline requires. It
checks them in one pass at startup, so a missing value surfaces immediately
instead of only when the pipeline runs — potentially much later.

The result is recorded on each pipeline as its `issues` (a missing secret is
reported against the task that declares it) and a computed `runnable`, and
served by the API as-is, so it isn't recomputed on every request. A warning is
logged too, naming each pipeline that can't run and why.

This is not a fatal error: the rest of the app starts normally, and only the
pipelines missing a secret are affected. When one of those does run, the task
raises where the secret is injected. A secret set after startup is picked up
on the next restart.

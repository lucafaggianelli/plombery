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

Instantiate the class wherever the value is needed. There is nothing else to
call: the class *is* the declaration, so it's read wherever you'd already
look for it, IDE autocomplete included.

```py
from plombery import task

from .secrets import WarehouseSecrets


@task
def load_to_warehouse(rows):
    secrets = WarehouseSecrets()
    engine = create_engine(secrets.WAREHOUSE_URI.get_secret_value())
    ...
```

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

Group secrets by what uses them, not all in one class. A common pattern is
one class per external system, in a dedicated module:

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

Only the classes a given task actually instantiates are resolved, so a task
that doesn't need the weather API never requires `WEATHER_API_KEY` to be set.

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseSecrets(BaseSettings):
    """Base class for declaring the secrets a pipeline or task needs, typed.

    A subclass is a plain schema: no YAML, no code generation, the class *is*
    the declaration, the same way `Pipeline.params` already works. A field's
    value is read from the environment variable of the same name (case
    insensitive, no prefix), or from a `.env` file in the current working
    directory:

        class WarehouseSecrets(BaseSecrets):
            WAREHOUSE_URI: SecretStr

        secrets = WarehouseSecrets()
        engine = create_engine(secrets.WAREHOUSE_URI.get_secret_value())

    Declare a field as `pydantic.SecretStr` to keep its value out of
    `repr()`/logs; `BaseSecrets` doesn't do this for you, since not every
    secret-shaped value (an API key that must be a plain `str` for some
    client library, say) can be a `SecretStr`.

    Where values come from is a `pydantic_settings` concern — the environment
    and `.env` are two of its sources. A backend such as a cloud secret
    manager (GCP Secret Manager, Infisical, ...) is added the same way the
    system settings add their YAML file: by overriding
    `settings_customise_sources` on a base class to append a custom source.
    A pipeline's own `BaseSecrets` subclasses and the way tasks declare and
    receive secrets don't change when a backend is added — only where the
    values are looked up does.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

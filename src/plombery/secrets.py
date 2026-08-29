from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseSecrets(BaseSettings):
    """Base class for declaring the secrets a pipeline or task needs, typed.

    A subclass is a plain schema: no YAML, no code generation, the class *is*
    the declaration, the same way `Pipeline.params` already works. Values are
    read from environment variables prefixed `PLOMBERY_SECRET_` (case
    insensitive), or from a `.env` file in the current working directory —
    the same two sources `plombery.config.yaml` itself is read from.

        class WarehouseSecrets(BaseSecrets):
            WAREHOUSE_URI: SecretStr

        secrets = WarehouseSecrets()
        engine = create_engine(secrets.WAREHOUSE_URI.get_secret_value())

    Declare a field as `pydantic.SecretStr` to keep its value out of
    `repr()`/logs; `BaseSecrets` doesn't do this for you, since not every
    secret-shaped value (an API key that must be a plain `str` for some
    client library, say) can be a `SecretStr`.
    """

    model_config = SettingsConfigDict(
        env_prefix="PLOMBERY_SECRET_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

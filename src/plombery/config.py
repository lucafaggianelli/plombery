from typing import Dict, Any, List, Tuple, Optional
import os
from pathlib import Path
import re
from yaml import load

try:
    # if libyaml is installed
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from pydantic import AnyHttpUrl, BaseModel, BaseSettings, HttpUrl, SecretStr
from pydantic.env_settings import SettingsSourceCallable

from plombery.schemas import NotificationRule

BASE_SETTINGS_FOLDER = Path()
SETTINGS_FILE_NAME = "plombery.config"
ENV_VAR_MATCHER = re.compile(r"\$(\w+|\{[^}]*\})")


def path_constructor(loader, node):
    return os.path.expandvars(node.value)


class EnvVarLoader(SafeLoader):
    pass


EnvVarLoader.add_implicit_resolver("!env", ENV_VAR_MATCHER, None)
EnvVarLoader.add_constructor("!env", path_constructor)


SUPPORTED_CONFIG_FILES: Tuple[Tuple[str, str]] = (
    ("yaml", "yaml"),
    ("yml", "yaml"),
)


def settings_file_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    A settings source that loads variables from a YAML file
    at the project's root.
    """

    from dotenv import load_dotenv

    # Load the env vars explicitely as pydantic reads env vars
    # locally without loading them into the system
    load_dotenv(settings.__config__.env_file)

    # Find user's defined config file among the supported ones
    for [ext, file_type] in SUPPORTED_CONFIG_FILES:
        config_file = BASE_SETTINGS_FOLDER / f"{SETTINGS_FILE_NAME}.{ext}"
        if config_file.exists():
            break
    else:
        # Any config file has been found
        return dict()

    encoding = settings.__config__.env_file_encoding

    with config_file.open(mode="r", encoding=encoding) as f:
        # `or {}` because the file may be empty
        return load(f, Loader=EnvVarLoader) or {}


class AuthSettings(BaseModel):
    client_id: SecretStr
    client_secret: SecretStr
    server_metadata_url: Optional[HttpUrl]
    access_token_url: Optional[HttpUrl]
    authorize_url: Optional[HttpUrl]
    jwks_uri: Optional[HttpUrl]
    client_kwargs: Optional[Any]
    secret_key: Optional[SecretStr] = SecretStr("not-very-secret-string")


class Settings(BaseSettings):
    auth: Optional[AuthSettings]
    database_url: str = "sqlite:///./plombery.db"
    notifications: Optional[List[NotificationRule]]
    server_url: Optional[AnyHttpUrl] = "http://localhost:8000"
    frontend_url: Optional[AnyHttpUrl] = "http://localhost:8000"

    class Config:
        env_file = BASE_SETTINGS_FOLDER / ".env"
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            **kwargs,
        ):
            return (
                init_settings,
                env_settings,
                settings_file_source,
            )


settings = Settings()

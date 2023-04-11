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

from pydantic import BaseSettings
from pydantic.env_settings import SettingsSourceCallable

from mario.notifications import NotificationRule

BASE_SETTINGS_FOLDER = Path()
SETTINGS_FILE_NAME = "mario.config"
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

    # Load the env vars explicitely as pydantic uses the
    load_dotenv(settings.__config__.env_file)

    for [ext, file_type] in SUPPORTED_CONFIG_FILES:
        config_file = BASE_SETTINGS_FOLDER / f"{SETTINGS_FILE_NAME}.{ext}"
        if config_file.exists():
            break
    else:
        # Any config file has been found
        return dict()

    encoding = settings.__config__.env_file_encoding

    with config_file.open(mode="r", encoding=encoding) as f:
        return load(f, Loader=EnvVarLoader)


class Settings(BaseSettings):
    database_url: str = "sqlite:///./mario.db"
    notifications: Optional[List[NotificationRule]]

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

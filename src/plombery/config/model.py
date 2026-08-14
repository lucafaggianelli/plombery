from pathlib import Path
from typing import Any, List, Literal, Optional, Tuple, Type, Union

from pydantic import AnyHttpUrl, AnyUrl, BaseModel, Field, HttpUrl, SecretStr
from pydantic_core import Url
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import PydanticBaseSettingsSource

from plombery.config.parser import SettingsFileSource
from plombery.schemas import NotificationRule

BASE_SETTINGS_FOLDER = Path()


class AuthSettings(BaseModel):
    client_id: SecretStr
    client_secret: SecretStr
    provider: Optional[str] = None
    server_metadata_url: Optional[HttpUrl] = None
    access_token_url: Optional[HttpUrl] = None
    authorize_url: Optional[HttpUrl] = None
    jwks_uri: Optional[HttpUrl] = None
    client_kwargs: Optional[Any] = None
    secret_key: SecretStr = SecretStr("not-very-secret-string")
    microsoft_tenant_id: Optional[str] = None


class RetentionSettings(BaseModel):
    """How long to keep the data produced by pipeline runs.

    The two thresholds are independent on purpose: log files are usually the
    first thing that stops being useful, while the run history is what feeds
    the charts and is worth keeping much longer.
    """

    files_days: Optional[int] = Field(
        default=None,
        gt=0,
        description=(
            "Delete the log files of runs finished more than this many days "
            "ago. The run itself is kept, so its history stays visible."
        ),
    )

    runs_days: Optional[int] = Field(
        default=None,
        gt=0,
        description=(
            "Delete the runs finished more than this many days ago, with "
            "their task runs, their stored outputs and their log files."
        ),
    )


class Settings(BaseSettings):
    auth: Optional[AuthSettings] = None
    blocked_loop_threshold: Optional[float] = Field(
        default=2.0,
        description=(
            "Log a warning when the event loop stays blocked for longer than "
            "this many seconds, naming the task responsible. An async task "
            "calling blocking code freezes the API and the live logs along "
            "with it, and this is what makes that visible. Set to 0 to disable."
        ),
    )
    retention: RetentionSettings = Field(default_factory=RetentionSettings)
    allowed_origins: Union[List[AnyHttpUrl], Literal["*"]] = "*"
    data_path: Path = Field(default_factory=Path.cwd)
    database_url: AnyUrl = AnyUrl("sqlite:///./plombery.db")
    database_auth_token: Optional[str] = None
    frontend_url: AnyHttpUrl = Url("http://localhost:8000")
    notifications: Optional[List[NotificationRule]] = None

    model_config = SettingsConfigDict(
        env_file=BASE_SETTINGS_FOLDER / ".env",
        env_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            file_secret_settings,
            SettingsFileSource(settings_cls),
        )

from pathlib import Path
from typing import Any, Literal

from pydantic import AnyHttpUrl, AnyUrl, BaseModel, Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import PydanticBaseSettingsSource

from plombery.config.parser import SettingsFileSource
from plombery.schemas import NotificationRule

BASE_SETTINGS_FOLDER = Path()


class AuthSettings(BaseModel):
    client_id: SecretStr
    client_secret: SecretStr
    provider: str | None = None
    server_metadata_url: HttpUrl | None = None
    access_token_url: HttpUrl | None = None
    authorize_url: HttpUrl | None = None
    jwks_uri: HttpUrl | None = None
    client_kwargs: Any | None = None
    secret_key: SecretStr = SecretStr("not-very-secret-string")
    microsoft_tenant_id: str | None = None


class RetentionSettings(BaseModel):
    """How long to keep the data produced by pipeline runs.

    The two thresholds are independent on purpose: log files are usually the
    first thing that stops being useful, while the run history is what feeds
    the charts and is worth keeping much longer.
    """

    files_days: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Delete the log files of runs finished more than this many days "
            "ago. The run itself is kept, so its history stays visible."
        ),
    )

    runs_days: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Delete the runs finished more than this many days ago, with "
            "their task runs, their stored outputs and their log files."
        ),
    )


class Settings(BaseSettings):
    auth: AuthSettings | None = None
    blocked_loop_threshold: float = Field(
        default=2.0,
        description=(
            "Log a warning when the event loop stays blocked for longer than "
            "this many seconds, naming the task responsible. An async task "
            "calling blocking code freezes the API and the live logs along "
            "with it, and this is what makes that visible. Set to 0 to disable."
        ),
    )
    retention: RetentionSettings = Field(default_factory=RetentionSettings)
    allowed_origins: list[AnyHttpUrl] | Literal["*"] = "*"
    data_path: Path = Field(default_factory=Path.cwd)
    database_url: AnyUrl = AnyUrl("sqlite:///./plombery.db")
    database_auth_token: str | None = None
    frontend_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8000")
    notifications: list[NotificationRule] | None = None
    pipeline_version: str | None = Field(
        default=None,
        description=(
            "The version recorded on every run, for the pipelines that don't "
            "declare one of their own. Set it to the revision the deployment "
            "was built from: an image ships without the git history Plombery "
            "would otherwise read the version from."
        ),
    )

    model_config = SettingsConfigDict(
        env_file=BASE_SETTINGS_FOLDER / ".env",
        env_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            file_secret_settings,
            SettingsFileSource(settings_cls),
        )

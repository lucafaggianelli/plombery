import logging
from pathlib import Path

from .api import app
from .notifications import NotificationRule, notification_manager
from .orchestrator import orchestrator
from .pipeline.pipeline import Task, Pipeline, PipelineRunStatus, Trigger  # noqa F401


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
_logger.addHandler(logging.StreamHandler())


class Mario:
    def __init__(self) -> None:
        self._load_configuration()

    def _load_configuration(self, config_file_name: str = None):
        config_file = Path(config_file_name or "mario.config.yml")

        from yaml import load

        try:
            # if libyaml is installed
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader

        if config_file.exists():
            _logger.info(f"Loading config from {config_file.absolute()}")
            with config_file.open("r", encoding="utf-8") as f:
                self._apply_config(load(f, Loader=Loader))

    def _apply_config(self, config: dict):
        for notification in config.get("notifications", []):
            self.add_notification_rule(NotificationRule(**notification))

    def register_pipeline(self, pipeline):
        orchestrator.register_pipeline(pipeline)

    def add_notification_rule(self, notification: NotificationRule):
        notification_manager.register_rule(notification)

    # Wrap FastAPI ASGI interface so the Mario object
    # can be served directly by uvicorn
    async def __call__(self, scope, receive, send):
        await app.__call__(scope, receive, send)

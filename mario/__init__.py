import logging

from .api import app
from .notifications import NotificationRule, notification_manager
from .orchestrator import orchestrator
from .pipeline.pipeline import Task, Pipeline, PipelineRunStatus, Trigger  # noqa F401
from .settings import Settings


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
_logger.addHandler(logging.StreamHandler())


class Mario:
    def __init__(self) -> None:
        self._load_settings()

    def _load_settings(self):
        settings = Settings()

        for notification in settings.notifications:
            self.add_notification_rule(notification)

    def register_pipeline(self, pipeline):
        orchestrator.register_pipeline(pipeline)

    def add_notification_rule(self, notification: NotificationRule):
        notification_manager.register_rule(notification)

    # Wrap FastAPI ASGI interface so the Mario object
    # can be served directly by uvicorn
    async def __call__(self, scope, receive, send):
        await app.__call__(scope, receive, send)

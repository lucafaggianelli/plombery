import logging


from .api import app
from .config import settings
from .logger import get_logger  # noqa F401
from .notifications import NotificationRule, notification_manager
from .orchestrator import orchestrator
from .pipeline import task, Task  # noqa F401
from .pipeline.pipeline import Pipeline, Trigger  # noqa F401
from .schemas import PipelineRunStatus  # noqa F401


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
_logger.addHandler(logging.StreamHandler())


class Mario:
    def __init__(self) -> None:
        self._apply_settings()
        orchestrator.start()

    def _apply_settings(self):
        for notification in settings.notifications or []:
            self.add_notification_rule(notification)

    def register_pipeline(self, pipeline):
        orchestrator.register_pipeline(pipeline)

    def add_notification_rule(self, notification: NotificationRule):
        notification_manager.register_rule(notification)

    # Wrap FastAPI ASGI interface so the Mario object
    # can be served directly by uvicorn
    async def __call__(self, scope, receive, send):
        await app.__call__(scope, receive, send)

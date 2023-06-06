from typing import List, Type
import logging
import os

from apscheduler.schedulers.base import SchedulerAlreadyRunningError
from pydantic import BaseModel

from .api import app
from .config import settings
from .logger import get_logger  # noqa F401
from .notifications import NotificationRule, notification_manager
from .orchestrator import orchestrator
from .pipeline import task, Task  # noqa F401
from .pipeline.pipeline import Pipeline, Trigger  # noqa F401
from .schemas import PipelineRunStatus  # noqa F401
from ._version import __version__  # noqa F401


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
_logger.addHandler(logging.StreamHandler())


if os.getenv("DEBUG_APS"):
    logging.basicConfig()
    logging.getLogger("apscheduler").setLevel(logging.DEBUG)


class _Plombery:
    def __init__(self) -> None:
        self._apply_settings()

    def _apply_settings(self):
        for notification in settings.notifications or []:
            self.add_notification_rule(notification)

    def register_pipeline(self, pipeline: Pipeline):
        orchestrator.register_pipeline(pipeline)

    def add_notification_rule(self, notification: NotificationRule):
        notification_manager.register_rule(notification)

    def stop(self):
        orchestrator.stop()

    # Wrap FastAPI ASGI interface so the Plombery object
    # can be served directly by uvicorn
    async def __call__(self, scope, receive, send):
        await app.__call__(scope, receive, send)


_app = _Plombery()


@app.on_event("startup")
def on_fastapi_start():
    try:
        orchestrator.start()
    except SchedulerAlreadyRunningError:
        pass


def get_app():
    return _app


def register_pipeline(
    id: str,
    tasks: List[Task],
    name: str = None,
    description: str = None,
    params: Type[BaseModel] = None,
    triggers: List[Trigger] = None,
):
    pipeline = Pipeline(
        id=id,
        tasks=tasks,
        name=name,
        description=description,
        params=params,
        triggers=triggers,
    )

    _app.register_pipeline(pipeline)

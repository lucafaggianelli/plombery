from typing import List, Optional, Type
import logging
import os

from apscheduler.schedulers.base import SchedulerAlreadyRunningError
from pydantic import BaseModel

from .api import app
from .config import settings
from .database.operations import setup_database
from .logger import get_logger  # noqa F401
from .notifications import NotificationRule, notification_manager
from .orchestrator import orchestrator
from .orchestrator.context import Context  # noqa F401
from .pipeline.tasks import Task, task, MappingMode  # noqa F401
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

    def start(self):
        setup_database()

        try:
            orchestrator.start()
        except SchedulerAlreadyRunningError:
            pass

    def stop(self):
        orchestrator.stop()


_plombery = _Plombery()


@app.on_event("startup")
def on_fastapi_start():
    _plombery.start()


def get_app():
    return app


def register_pipeline(
    id: str,
    tasks: List[Task],
    name: Optional[str] = None,
    description: Optional[str] = None,
    params: Optional[Type[BaseModel]] = None,
    triggers: Optional[List[Trigger]] = None,
):
    pipeline = Pipeline(
        id=id,
        tasks=tasks,
        name=name,
        description=description,
        params=params,
        triggers=triggers or [],
    )

    _plombery.register_pipeline(pipeline)

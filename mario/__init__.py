from typing import List

from .api import app
from .notifications import NotificationRule, notification_manager
from .orchestrator import orchestrator
from .pipeline.pipeline import Task, Pipeline, PipelineRunStatus, Trigger  # noqa F401


class Mario:
    def register_pipeline(self, pipeline):
        orchestrator.register_pipeline(pipeline)

    def add_notification_rule(
        self, status: List[PipelineRunStatus], channels: List[str]
    ):
        notification_manager.register_rule(
            NotificationRule(pipeline_status=status, channels=channels)
        )

    # Wrap FastAPI ASGI interface so the Mario object
    # can be served directly by uvicorn
    async def __call__(self, scope, receive, send):
        await app.__call__(scope, receive, send)

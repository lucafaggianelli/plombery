import logging
from typing import List
from apprise import Apprise, NotifyFormat
import apprise

from plombery.config import settings
from plombery.database.schemas import PipelineRun
from plombery.notifications.helpers import get_pipeline_status_verb
from plombery.notifications.templates import render_pipeline_run
from plombery.pipeline.pipeline import Pipeline
from plombery.schemas import NotificationRule, PipelineRunStatus


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


PIPELINE_STATUS_TO_VERB = {
    "running": "has started",
    "completed": "has successfully completed 👌",
    "failed": "failed ❌",
    "cancelled": "was cancelled",
}


def get_message_title(
    pipeline_name: str, pipeline_run_status: PipelineRunStatus
) -> str:
    return f"Pipeline {pipeline_name} {get_pipeline_status_verb(pipeline_run_status)}"


class NotificationManager:
    def __init__(self) -> None:
        self.rules: List[NotificationRule] = []

    def register_rule(self, rule: NotificationRule):
        self.rules.append(rule)

    def _get_applicable_rules(
        self, pipeline_run: PipelineRun
    ) -> List[NotificationRule]:
        return [
            rule for rule in self.rules if pipeline_run.status in rule.pipeline_status
        ]

    async def notify(self, pipeline: Pipeline, pipeline_run: PipelineRun):
        rules = self._get_applicable_rules(pipeline_run)

        if not rules:
            return

        title = get_message_title(pipeline.name, pipeline_run.status)
        html = render_pipeline_run(
            pipeline.name,
            get_pipeline_status_verb(pipeline_run.status),
            f"{settings.frontend_url}/pipelines/{pipeline_run.pipeline_id}/triggers/{pipeline_run.trigger_id}/runs/{pipeline_run.id}",
        )

        apobj = Apprise()

        for rule in rules:
            for channel in rule.channels:
                apobj.add(channel)

        with apprise.LogCapture(level=apprise.logging.INFO) as output:
            result = await apobj.async_notify(
                title=title,
                body=html,
                body_format=NotifyFormat.HTML,
            )

            if result:
                logger.info("Successfully sent notifications")
            else:
                logger.error(output.read())
                logger.error("Error sending notifications")


notification_manager = NotificationManager()

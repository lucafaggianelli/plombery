import logging
from typing import List
from apprise import Apprise
import apprise

from plombery.config import settings
from plombery.database.schemas import PipelineRun
from plombery.schemas import NotificationRule


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


PIPELINE_STATUS_TO_VERB = {
    "running": "has started",
    "completed": "has successfully completed 👌",
    "failed": "failed ❌",
    "cancelled": "was cancelled",
}


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

    async def notify(self, pipeline_run: PipelineRun):
        rules = self._get_applicable_rules(pipeline_run)

        if not rules:
            return

        apobj = Apprise()

        for rule in rules:
            for channel in rule.channels:
                apobj.add(channel)

        with apprise.LogCapture(level=apprise.logging.INFO) as output:
            result = await apobj.async_notify(
                title=f"[Plombery] Your pipeline {pipeline_run.pipeline_id} {PIPELINE_STATUS_TO_VERB[pipeline_run.status]}",
                body=f"""
    Your pipeline {pipeline_run.pipeline_id} {PIPELINE_STATUS_TO_VERB[pipeline_run.status]}

    To have more info: {settings.frontend_url}/pipelines/{pipeline_run.pipeline_id}/triggers/{pipeline_run.trigger_id}/runs/{pipeline_run.id}
    """,
            )

            if result:
                logger.info("Successfully sent notifications")
            else:
                logger.error(output.read())
                logger.error("Error sending notifications")


notification_manager = NotificationManager()

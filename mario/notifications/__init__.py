from typing import Any, Dict, List
import logging

from httpx import URL

from mario.config import settings
from mario.database.schemas import PipelineRun
from mario.notifications.send_email import send as send_email
from mario.notifications.send_msteams import send as send_msteams
from mario.pipeline.pipeline import Pipeline
from mario.schemas import NotificationRule, PipelineRunStatus
from .helpers import get_pipeline_status_verb


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


_SENDERS: Dict[str, Any] = {"mailto": send_email, "msteams": send_msteams}


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

        print(rules, pipeline_run.status)
        print(rules[0].channels)

        for rule in rules:
            for channel in rule.channels:
                channel = URL(channel)

                sender = _SENDERS.get(channel.scheme)

                if not sender:
                    logger.warn("Sender protocol %s not supported", channel.scheme)
                    continue

                print("Sending", channel)

                sender(
                    channel,
                    title,
                    data={
                        "pipeline": pipeline,
                        "pipeline_run": pipeline_run,
                        "pipeline_run_url": f"{settings.frontend_url}/pipelines/{pipeline_run.pipeline_id}/triggers/{pipeline_run.trigger_id}/runs/{pipeline_run.id}",
                        "status_verb": get_pipeline_status_verb(pipeline_run.status),
                    },
                )


notification_manager = NotificationManager()

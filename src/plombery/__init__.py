from typing import overload
import logging
import os

from apscheduler.schedulers.base import SchedulerAlreadyRunningError
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel, ValidationError

from .api import app
from .config import settings
from .database.operations import setup_database
from .logger import get_logger  # noqa F401
from .logger.web_socket_handler import bind_event_loop
from .notifications import NotificationRule, notification_manager
from .orchestrator import orchestrator
from .orchestrator.executor import check_task_signature
from .orchestrator.watchdog import start_watchdog, stop_watchdog
from .retention import apply_retention, delete_orphan_data
from .orchestrator.context import Context  # noqa F401
from .pipeline.tasks import Task, task, MappingMode, OutputOf  # noqa F401
from .pipeline.pipeline import Pipeline, Trigger  # noqa F401
from .schemas import PipelineIssue, PipelineRunStatus  # noqa F401
from .secrets import BaseSecrets  # noqa F401
from ._version import __version__  # noqa F401


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
_logger.addHandler(logging.StreamHandler())


if os.getenv("DEBUG_APS"):
    logging.basicConfig()
    logging.getLogger("apscheduler").setLevel(logging.DEBUG)


RETENTION_JOB_ID = "plombery:retention"


def _apply_retention():
    """Run the retention policy, never letting it take the app down with it."""

    try:
        apply_retention()
        delete_orphan_data()
    except Exception as error:
        _logger.error("Cannot apply the retention policy: %s", error, exc_info=error)


def _find_pipeline_issues(pipeline: Pipeline) -> list[PipelineIssue]:
    """The problems that keep a pipeline, or one of its tasks, from running.

    For now this is the secrets each task declares that aren't set. Inspecting
    a task's signature for `BaseSecrets`-annotated arguments is what turns a
    runtime failure into something known up front.
    """

    # secrets class -> the env var names it's missing ([] when satisfied)
    missing_by_class: dict = {}

    def missing_for(secrets_cls) -> list:
        if secrets_cls not in missing_by_class:
            try:
                secrets_cls()
                missing_by_class[secrets_cls] = []
            except ValidationError as error:
                missing_by_class[secrets_cls] = [
                    str(err["loc"][0]) for err in error.errors() if err["loc"]
                ]

        return missing_by_class[secrets_cls]

    issues: list[PipelineIssue] = []

    for pipeline_task in pipeline.tasks:
        signature = check_task_signature(pipeline_task.run)

        for secrets_cls in signature.secret_args.values():
            for name in missing_for(secrets_cls):
                issues.append(
                    PipelineIssue(
                        level="error",
                        code="missing_secret",
                        message=(
                            f"Secret '{name}' (from {secrets_cls.__name__}) is not "
                            f"set, so task '{pipeline_task.id}' can't run."
                        ),
                        task_id=pipeline_task.id,
                    )
                )

    return issues


def check_registered_pipelines() -> None:
    """Check every registered pipeline once and store the result on it.

    Populates `pipeline.issues` so the API can serve it — and the UI show which
    pipelines are runnable and why — without recomputing on every request.
    Called at startup; a fix (a secret now set) is picked up on the next
    restart. Not fatal: the app comes up, and only the affected pipelines
    can't run.
    """

    for pipeline in orchestrator.pipelines.values():
        pipeline.issues = _find_pipeline_issues(pipeline)

        errors = [issue for issue in pipeline.issues if issue.level == "error"]
        if errors:
            _logger.warning(
                "Pipeline '%s' can't run: %s",
                pipeline.id,
                "; ".join(issue.message for issue in errors),
            )


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
        # Socket.IO coroutines are scheduled onto this loop from the logging
        # thread, so it has to be captured while it is running.
        bind_event_loop()
        start_watchdog(settings.blocked_loop_threshold)

        setup_database()

        _apply_retention()

        # Every pipeline has registered by now (registration happens at import,
        # this runs on the FastAPI startup event), so each one can be checked
        # once and its result stored on it.
        check_registered_pipelines()

        try:
            orchestrator.start()
        except SchedulerAlreadyRunningError:
            pass

        # Keep reclaiming space while the app is up, not only at boot: a long
        # running instance would otherwise never apply the policy.
        orchestrator.scheduler.add_job(
            _apply_retention,
            trigger=IntervalTrigger(days=1),
            id=RETENTION_JOB_ID,
            name=RETENTION_JOB_ID,
            replace_existing=True,
        )

    def stop(self):
        stop_watchdog()
        orchestrator.stop()


_plombery = _Plombery()


@app.on_event("startup")
def on_fastapi_start():
    _plombery.start()


def get_app():
    return app


@overload
def register_pipeline(id: Pipeline) -> Pipeline:
    """Register a `Pipeline` already built, typically with the `with Pipeline()` context manager."""


@overload
def register_pipeline(
    id: str,
    tasks: list[Task],
    name: str | None = None,
    description: str | None = None,
    params: type[BaseModel] | None = None,
    triggers: list[Trigger] | None = None,
) -> Pipeline:
    """Build and register a pipeline from its parts, the flat alternative to the context manager."""


def register_pipeline(
    id: str | Pipeline,
    tasks: list[Task] | None = None,
    name: str | None = None,
    description: str | None = None,
    params: type[BaseModel] | None = None,
    triggers: list[Trigger] | None = None,
) -> Pipeline:
    if isinstance(id, Pipeline):
        pipeline = id
    else:
        pipeline = Pipeline(
            id=id,
            tasks=tasks or [],
            name=name,
            description=description,
            params=params,
            triggers=triggers or [],
        )

    _plombery.register_pipeline(pipeline)

    return pipeline

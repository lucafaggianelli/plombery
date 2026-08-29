from typing import List, Optional, Type, Union, overload
import logging
import os

from apscheduler.schedulers.base import SchedulerAlreadyRunningError
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel

from .api import app
from .config import settings
from .database.operations import setup_database
from .logger import get_logger  # noqa F401
from .logger.web_socket_handler import bind_event_loop
from .notifications import NotificationRule, notification_manager
from .orchestrator import orchestrator
from .orchestrator.watchdog import start_watchdog, stop_watchdog
from .retention import apply_retention, delete_orphan_data
from .orchestrator.context import Context  # noqa F401
from .pipeline.tasks import Task, task, MappingMode, OutputOf  # noqa F401
from .pipeline.pipeline import Pipeline, Trigger  # noqa F401
from .schemas import PipelineRunStatus  # noqa F401
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


def get_pipelines_missing_secrets() -> dict:
    """Which registered pipelines can't run because a secret they need is unset.

    Returns a mapping of pipeline id -> {secrets class name -> missing env var
    names}; a pipeline with everything it declares available is absent from it.
    Computed by inspecting each task's signature for `BaseSecrets`-annotated
    arguments and constructing each distinct class once.

    Meant to be called once every pipeline is registered — at server startup,
    and by the API so the UI can show which pipelines are runnable.
    """

    from pydantic import ValidationError
    from plombery.orchestrator.executor import check_task_signature

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

    result: dict = {}

    for pipeline in orchestrator.pipelines.values():
        for pipeline_task in pipeline.tasks:
            signature = check_task_signature(pipeline_task.run)

            for secrets_cls in signature.secret_args.values():
                missing = missing_for(secrets_cls)

                if missing:
                    result.setdefault(pipeline.id, {})[secrets_cls.__name__] = missing

    return result


def _report_missing_secrets():
    """Warn, at startup, about pipelines that can't run for lack of a secret.

    Not fatal on purpose: the rest of the app comes up, the affected pipelines
    are named so they can be fixed, and the same information is available to
    the UI through `get_pipelines_missing_secrets`.
    """

    for pipeline_id, by_class in get_pipelines_missing_secrets().items():
        details = "; ".join(
            f"{cls} ({', '.join(names)})" for cls, names in by_class.items()
        )
        _logger.warning(
            "Pipeline '%s' is missing secrets and won't run until they are set: %s",
            pipeline_id,
            details,
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
        # this runs on the FastAPI startup event), so the secrets each one needs
        # can be checked in one pass.
        _report_missing_secrets()

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
def register_pipeline(pipeline: Pipeline) -> Pipeline:
    """Register a `Pipeline` already built, typically with the `with Pipeline()` context manager."""


@overload
def register_pipeline(
    id: str,
    tasks: List[Task],
    name: Optional[str] = None,
    description: Optional[str] = None,
    params: Optional[Type[BaseModel]] = None,
    triggers: Optional[List[Trigger]] = None,
) -> Pipeline:
    """Build and register a pipeline from its parts, the flat alternative to the context manager."""


def register_pipeline(
    id: Union[str, Pipeline],
    tasks: Optional[List[Task]] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    params: Optional[Type[BaseModel]] = None,
    triggers: Optional[List[Trigger]] = None,
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

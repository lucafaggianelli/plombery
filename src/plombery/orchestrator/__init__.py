from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from plombery.constants import MANUAL_TRIGGER_ID
from plombery.database.models import PipelineRun
from plombery.database.repository import create_pipeline_run
from plombery.database.schemas import PipelineRunCreate
from plombery.orchestrator.executor import Pipeline, run, Trigger, utcnow
from plombery.pipeline._utils import get_job_id
from plombery.schemas import PipelineRunStatus


class _Orchestrator:
    _all_pipelines: Dict[str, Pipeline] = {}
    _all_triggers: Dict[str, Tuple[Pipeline, Trigger]] = {}

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()

    def register_pipeline(self, pipeline: Pipeline):
        if pipeline.id in self._all_pipelines:
            print(f"Pipeline {pipeline.id} already registered")
            return

        self._all_pipelines[pipeline.id] = pipeline

        for trigger in pipeline.triggers:
            if trigger.paused:
                continue

            job_id = get_job_id(pipeline.id, trigger.id)
            self._all_triggers[job_id] = (pipeline, trigger)

            if self.scheduler.get_job(job_id):
                print(f"Job {job_id} already added")
                continue

            self.scheduler.add_job(
                id=job_id,
                name=job_id,
                func=run,
                trigger=trigger.schedule,
                kwargs=dict(pipeline=pipeline, trigger=trigger),
                # run once instead of many times if the scheduler determines that the
                # job should be run more than once in succession
                coalesce=True,
                # Jobs will be run even if they arrive 1 min late
                misfire_grace_time=timedelta(minutes=1).seconds,
                max_instances=10_000,
            )

    def get_pipeline(self, pipeline_id: str):
        """Finds a registered pipeline by its ID,
        it returns None if the pipeline is not found"""
        return self._all_pipelines.get(pipeline_id)

    @property
    def pipelines(self):
        return self._all_pipelines

    def get_pipeline_from_job_id(self, job_id: str):
        return self._all_triggers[job_id][0]

    def get_trigger_from_job_id(self, job_id: str):
        return self._all_triggers[job_id][1]

    def get_job(self, pipeline_id, trigger_id) -> Optional[Job]:
        return self.scheduler.get_job(get_job_id(pipeline_id, trigger_id))

    def start(self):
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown(wait=False)


orchestrator = _Orchestrator()


async def run_pipeline_now(
    pipeline: Pipeline, trigger: Optional[Trigger] = None, params: Any = None
) -> PipelineRun:
    trigger_id = trigger.id if trigger else MANUAL_TRIGGER_ID

    pipeline_run = create_pipeline_run(
        PipelineRunCreate(
            start_time=utcnow(),
            pipeline_id=pipeline.id,
            trigger_id=trigger_id,
            status=PipelineRunStatus.PENDING,
        )
    )

    executor: AsyncIOExecutor = orchestrator.scheduler._lookup_executor("default")
    executor.submit_job(
        Job(
            orchestrator.scheduler,
            id=get_job_id(pipeline.id, trigger_id),
            func=run,
            args=[],
            kwargs={
                "pipeline": pipeline,
                "trigger": trigger,
                "params": params,
                "pipeline_run": pipeline_run,
            },
            max_instances=10_000,
            misfire_grace_time=None,
            trigger=DateTrigger(),
        ),
        [datetime.now()],
    )

    return pipeline_run

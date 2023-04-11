from datetime import datetime
from typing import Any, Dict, Tuple

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from mario.constants import MANUAL_TRIGGER_ID
from mario.orchestrator.executor import Pipeline, run, Trigger


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

            job_id = f"{pipeline.id}: {trigger.id}"
            self._all_triggers[job_id] = (pipeline, trigger)

            if self.scheduler.get_job(job_id):
                print(f"Job {job_id} already added")
                continue

            self.scheduler.add_job(
                id=job_id,
                func=run,
                trigger=trigger.aps_trigger,
                kwargs=dict(pipeline=pipeline, trigger=trigger),
                coalesce=True,
            )

    def get_pipeline(self, pipeline_id: str):
        return self._all_pipelines[pipeline_id]

    @property
    def pipelines(self):
        return self._all_pipelines

    def get_pipeline_from_job_id(self, job_id: str):
        return self._all_triggers[job_id][0]

    def get_trigger_from_job_id(self, job_id: str):
        return self._all_triggers[job_id][1]

    def start(self):
        self.scheduler.start()


orchestrator = _Orchestrator()


async def run_pipeline_now(
    pipeline: Pipeline, trigger: Trigger = None, params: Any = None
):
    executor: AsyncIOExecutor = orchestrator.scheduler._lookup_executor("default")
    executor.submit_job(
        Job(
            orchestrator.scheduler,
            id=f"{pipeline.id}: {MANUAL_TRIGGER_ID}",
            func=run,
            args=[],
            kwargs={"pipeline": pipeline, "trigger": trigger, "params": params},
            max_instances=1,
            misfire_grace_time=None,
            trigger=DateTrigger(),
        ),
        [datetime.now()],
    )

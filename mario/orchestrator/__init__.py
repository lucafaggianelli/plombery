from typing import Dict, Tuple
from datetime import datetime

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobEvent
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from mario.database.repository import update_pipeline_run
from mario.orchestrator.executor import Pipeline, run, Trigger


class _Orchestrator:
    _all_pipelines: Dict[str, Pipeline] = {}
    _all_triggers: Dict[str, Tuple[Pipeline, Trigger]] = {}

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()

    def register_pipeline(self, pipeline: Pipeline):
        if pipeline.uuid in self._all_pipelines:
            print(f"Pipeline {pipeline.uuid} already registered")
            return

        self._all_pipelines[pipeline.uuid] = pipeline

        for trigger in pipeline.triggers:
            if trigger.paused:
                continue

            job_id = f"{pipeline.uuid}: {trigger.name}"
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
        self.scheduler.add_listener(
            on_job_completed, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        self.scheduler.start()


orchestrator = _Orchestrator()


def on_job_completed(event: JobEvent):
    pipeline = orchestrator.get_pipeline_from_job_id(event.job_id)
    trigger = orchestrator.get_trigger_from_job_id(event.job_id)

    status = None

    if event.code == EVENT_JOB_EXECUTED:
        status = "success"
    elif event.code == EVENT_JOB_ERROR:
        status = "fail"

    update_pipeline_run(pipeline.uuid, trigger.name, datetime.now(), status)


orchestrator.start()

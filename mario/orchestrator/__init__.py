from typing import Dict, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler

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


orchestrator.start()

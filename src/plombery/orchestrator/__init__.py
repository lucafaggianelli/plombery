from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from plombery.constants import MANUAL_TRIGGER_ID
from plombery.database.models import PipelineRun
from plombery.database.repository import (
    create_pipeline_run,
    create_task_run,
    get_active_task_runs,
    get_task_run_by_id_and_run_id,
    get_task_runs_for_pipeline_run,
)
from plombery.database.schemas import PipelineRunCreate, TaskRunCreate
from plombery.orchestrator.executor import (
    Pipeline,
    execute_task_instance,
    on_pipeline_status_changed,
    run,
    Trigger,
    utcnow,
)
from plombery.pipeline._utils import get_job_id
from plombery.pipeline.task import Task
from plombery.schemas import PipelineRunStatus
from plombery.websocket import sio


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

    def start_pipeline_tasks(
        self,
        pipeline: Pipeline,
        pipeline_run: PipelineRun,
        initial_params: Optional[Dict[str, Any]] = None,
    ):
        """
        Submits tasks with no upstream dependencies to the Executor.
        Called by executor.run() after setup.
        """

        # Find tasks with no dependencies (DAG entry points)
        initial_tasks = [task for task in pipeline.tasks if not task.upstream_task_ids]

        for task in initial_tasks:
            self._schedule_task_instance(
                pipeline,
                pipeline_run,
                task,
                resolved_context={"params": initial_params},
            )

    async def handle_task_completion(
        self, pipeline_run: PipelineRun, completed_task_id: str
    ):
        """
        Checks dependencies for downstream tasks and schedules them if ready.
        Also checks if the entire pipeline run is complete.
        """
        await sio.emit(
            "run-update",
            dict(
                pipeline=pipeline_run.pipeline_id,
                trigger=pipeline_run.trigger_id,
            ),
        )

        pipeline = self.get_pipeline(pipeline_run.pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_run.pipeline_id} not found")

        completed_task = pipeline.get_task_by_id(completed_task_id)
        if not completed_task:
            raise ValueError(f"Task {completed_task_id} not found")

        # If the pipeline was already marked FAILED by a previous task, stop.
        if pipeline_run.status != PipelineRunStatus.RUNNING:
            return

        completed_task_run = get_task_run_by_id_and_run_id(
            completed_task_id, pipeline_run.id
        )
        if not completed_task_run:
            raise ValueError(
                f"TaskRun {completed_task_id} not found for run {pipeline_run.id}"
            )

        if completed_task_run.status == PipelineRunStatus.FAILED:
            # Mark the entire pipeline as failed and stop
            on_pipeline_status_changed(pipeline, pipeline_run, PipelineRunStatus.FAILED)
            return

        downstream_task_ids = [
            task.id
            for task in pipeline.tasks
            if completed_task_run.task_id in task.upstream_task_ids
        ]

        # Process Downstream Tasks
        for downstream_task_id in downstream_task_ids:
            downstream_task = pipeline.get_task_by_id(downstream_task_id)

            if not downstream_task:
                raise ValueError(f"Task {downstream_task_id} not found")

            # Check if ALL upstream tasks for the downstream task are complete
            if self._are_upstream_tasks_complete(pipeline_run.id, downstream_task):
                self._schedule_task_instance(
                    pipeline, pipeline_run, downstream_task, {}
                )

        # 4. Final Pipeline Run Completion Check
        active_tasks = get_active_task_runs(
            pipeline_run.id
        )  # Assuming a repo method for this
        if not active_tasks:
            # No more running, scheduled, or pending tasks left
            on_pipeline_status_changed(
                pipeline, pipeline_run, PipelineRunStatus.COMPLETED
            )

    def _are_upstream_tasks_complete(self, run_id: int, task: Task) -> bool:
        """Verifies all dependencies are met."""
        upstream_runs = get_task_runs_for_pipeline_run(run_id, task.upstream_task_ids)

        # If any required upstream run is missing or not 'COMPLETED', return False
        if len(upstream_runs) != len(task.upstream_task_ids):
            return False  # Not all upstream tasks have even started/finished yet

        for up_run in upstream_runs:
            if up_run.status != PipelineRunStatus.COMPLETED:
                return False
        return True

    def _schedule_task_instance(
        self,
        pipeline: Pipeline,
        pipeline_run: PipelineRun,
        task: Task,
        resolved_context: Dict[str, Any],
    ):
        """Creates TaskRun record and submits job to executor."""

        # 1. Create TaskRun DB record
        task_run_db = create_task_run(
            TaskRunCreate(
                pipeline_run_id=pipeline_run.id,
                task_id=task.id,
                status=PipelineRunStatus.PENDING,
                # Store resolved inputs for the executor to use
                context=resolved_context,
            )
        )

        # Submit job to APScheduler/Executor
        executor: AsyncIOExecutor = self.scheduler._lookup_executor("default")

        job_id = get_job_id(pipeline.id, f"{task.id}_{task_run_db.id}")

        executor.submit_job(
            Job(
                self.scheduler,
                id=job_id,
                func=execute_task_instance,
                args=[],
                kwargs={
                    "pipeline": pipeline,
                    "task": task,
                    "pipeline_run": pipeline_run,
                    # "task_run_id": task_run_db.id,
                },
                max_instances=10_000,
                misfire_grace_time=None,
                trigger=DateTrigger(),
            ),
            [datetime.now()],
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
    pipeline: Pipeline,
    trigger: Optional[Trigger] = None,
    params: Any = None,
    reason: str = "api",
) -> PipelineRun:
    trigger_id = trigger.id if trigger else MANUAL_TRIGGER_ID

    pipeline_run = create_pipeline_run(
        PipelineRunCreate(
            start_time=utcnow(),
            pipeline_id=pipeline.id,
            trigger_id=trigger_id,
            status=PipelineRunStatus.PENDING,
            input_params=params,
            reason=reason,
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

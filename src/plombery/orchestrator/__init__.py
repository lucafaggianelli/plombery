from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from plombery.constants import MANUAL_TRIGGER_ID
from plombery.database.models import PipelineRun, TaskRun
from plombery.database.repository import (
    create_pipeline_run,
    create_task_run,
    get_task_run_output_by_id,
    get_task_runs_for_pipeline_run,
    mark_tasks_as_skipped,
)
from plombery.database.schemas import PipelineRunCreate, TaskRunCreate
from plombery.orchestrator.dag import is_mappable_list
from plombery.orchestrator.executor import (
    Pipeline,
    execute_task_instance,
    on_pipeline_status_changed,
    run,
    Trigger,
)
from plombery.pipeline._utils import get_job_id
from plombery.pipeline.tasks import MappingMode, Task
from plombery.schemas import FINISHED_STATUS, PipelineRunStatus
from plombery.utils import utcnow
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

    async def handle_task_completion(self, task_run: TaskRun):
        """
        Checks dependencies for downstream tasks and schedules them if ready.
        Also checks if the entire pipeline run is complete.
        """
        await sio.emit(
            "run-update",
            dict(
                pipeline=task_run.pipeline_run.pipeline_id,
                trigger=task_run.pipeline_run.trigger_id,
            ),
        )

        pipeline = self.get_pipeline(task_run.pipeline_run.pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {task_run.pipeline_run.pipeline_id} not found")

        completed_task = pipeline.get_task_by_id(task_run.task_id)
        if not completed_task:
            raise ValueError(f"Task {task_run.task_id} not found")

        # If the pipeline was already marked FAILED by a previous task, stop.
        if task_run.pipeline_run.status != PipelineRunStatus.RUNNING:
            return

        if task_run.task_output_id:
            task_output = get_task_run_output_by_id(task_run.task_output_id)
            output_data = task_output.data if task_output else None
            mappable_list = is_mappable_list(output_data)
        else:
            output_data = None
            mappable_list = False

        # Metadata about the run instance that just completed
        completed_was_mapped_instance = task_run.map_index is not None
        instance_map_index = task_run.map_index

        if task_run.status == PipelineRunStatus.FAILED:
            # Mark the entire pipeline as failed and stop
            on_pipeline_status_changed(
                pipeline, task_run.pipeline_run, PipelineRunStatus.FAILED
            )
            return

        downstream_task_ids = [
            task.id
            for task in pipeline.tasks
            if task_run.task_id in task.upstream_task_ids
        ]

        skipped_tasks: list[Task] = []

        # Process Downstream Tasks
        for downstream_task_id in downstream_task_ids:
            downstream_task = pipeline.get_task_by_id(downstream_task_id)

            if not downstream_task:
                raise ValueError(f"Task {downstream_task_id} not found")

            # Check if Downstream task is explicitly configured to map
            # using Completed Task's output
            is_mapped_downstream = (
                downstream_task.mapping_mode
                and downstream_task.map_upstream_id == task_run.task_id
            )

            # TODO: What if a mapped task has more than 1 upstream?
            if is_mapped_downstream:

                # Case A: Fan-Out Per Item (Initial or Nested):
                # The completed task output is an array and the downstream
                # task will run 1 time per each item of the array
                if downstream_task.mapping_mode == MappingMode.FAN_OUT:

                    if not mappable_list:
                        # List required for fan-out: this is an error
                        raise ValueError(
                            f"Task {downstream_task.id} expected a collection for fan-out, but got {type(output_data)}"
                        )

                    if not output_data:
                        # The upstream task returned an empty list so
                        # the downstream mapped tasks cannot instantiated
                        skipped_tasks.append(downstream_task)
                        continue

                    # Schedule a new run for each item in the output list.
                    for index, _ in enumerate(output_data):
                        self._schedule_task_instance(
                            pipeline,
                            task_run.pipeline_run,
                            downstream_task,
                            parent_task_run_id=task_run.task_id,
                            map_index=index,
                        )

                # Case B: Chained Fan-Out (Inheriting the Index)
                # The completed task was fan-out from an array (Case A) so
                # instead of fan-in, this task keep inheriting the mapping index from
                # the parent and will process 1 item at a time
                elif downstream_task.mapping_mode == MappingMode.CHAINED_FAN_OUT:

                    if not completed_was_mapped_instance:
                        raise ValueError(
                            f"Task {downstream_task.id} expected upstream task {completed_task.id} to be a mapped instance: cannot chain."
                        )

                    # Schedule EXACTLY ONE run, inheriting the index from the parent instance
                    self._schedule_task_instance(
                        pipeline,
                        task_run.pipeline_run,
                        downstream_task,
                        parent_task_run_id=task_run.task_id,
                        map_index=instance_map_index,  # Inherit the map_index
                    )

                else:
                    raise ValueError(
                        f"Invalid mapping mode {downstream_task.mapping_mode}"
                    )

            # Check if ALL upstream tasks for the downstream task are complete
            elif self._are_upstream_tasks_complete(
                task_run.pipeline_run_id, downstream_task
            ):
                self._schedule_task_instance(
                    pipeline,
                    task_run.pipeline_run,
                    downstream_task,
                )

            else:
                print(f"Downstream task {downstream_task.id} not ready")
                # Instantiate the task anyway so the it's marked into the DB

        # Check if the pipeline has finished running, checking if all the tasks have finished
        #
        # The check is pretty tricky as tasks get scheduled dynamically and task runs are
        # inserted in the DB just before the task is queued.
        # Even more, some tasks are mapped so their task runs appear more than once.

        finished_tasks = get_finished_tasks_ids(task_run.pipeline_run_id)

        # Skipped tasks for the moment are mapped tasks whose upstream output is an empty list
        # so they cannot be scheduled

        all_skipped_tasks: set[str] = set()

        for task in skipped_tasks:
            all_skipped_tasks.add(task.id)
            all_skipped_tasks = all_skipped_tasks.union(
                get_downstream_task_ids(task.id, pipeline)
            )
            finished_tasks.extend(all_skipped_tasks)

        mark_tasks_as_skipped(all_skipped_tasks, task_run.pipeline_run_id)

        if len(finished_tasks) == len(pipeline.tasks):
            # No more running, scheduled, or pending tasks left
            on_pipeline_status_changed(
                pipeline, task_run.pipeline_run, PipelineRunStatus.COMPLETED
            )

    def _are_upstream_tasks_complete(self, pipeline_run_id: int, task: Task) -> bool:
        """Verifies all dependencies are met."""
        finished_tasks = get_task_runs_for_pipeline_run(
            pipeline_run_id,
            task.upstream_task_ids,
            status=[PipelineRunStatus.COMPLETED],
        )

        ready = len(finished_tasks) == len(task.upstream_task_ids)

        if not ready:
            print(
                f"Upstream tasks of {task.id} not ready because",
                set(task.upstream_task_ids) - set(finished_tasks),
            )

        return ready

    def _schedule_task_instance(
        self,
        pipeline: Pipeline,
        pipeline_run: PipelineRun,
        task: Task,
        resolved_context: Optional[Dict[str, Any]] = None,
        parent_task_run_id: Optional[str] = None,
        map_index: Optional[int] = None,
    ):
        """Creates TaskRun record and submits job to executor."""

        # 1. Create TaskRun DB record
        task_run_db = create_task_run(
            TaskRunCreate(
                pipeline_run_id=pipeline_run.id,
                task_id=task.id,
                status=PipelineRunStatus.PENDING,
                context=resolved_context,
                parent_task_run_id=parent_task_run_id,
                map_index=map_index,
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
                    "task_run_id": task_run_db.id,
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


def get_downstream_task_ids(task_id: str, pipeline: Pipeline):
    """Given a task ID it finds all downstream tasks at any level in a pipeline"""

    task = pipeline.get_task_by_id(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")

    downstream_tasks = task.downstream_task_ids.copy()

    for ds_task in task.downstream_task_ids:
        downstream_tasks = downstream_tasks.union(
            get_downstream_task_ids(ds_task, pipeline)
        )

    return downstream_tasks


def get_finished_tasks_ids(pipeline_run_id: int, task_ids: Optional[list[str]] = None):
    tasks_status: dict[str, bool] = {}

    for r in get_task_runs_for_pipeline_run(pipeline_run_id, task_ids):
        if tasks_status.get(r.task_id) is not False:
            tasks_status[r.task_id] = r.status in FINISHED_STATUS

    finished_tasks = [task_id for task_id, finished in tasks_status.items() if finished]

    return finished_tasks


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

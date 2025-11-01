from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone
import inspect

from pydantic import BaseModel

from plombery.constants import MANUAL_TRIGGER_ID
from plombery.exceptions import InvalidDataPath
from plombery.logger import close_logger, get_logger
from plombery.notifications import notification_manager
from plombery.orchestrator.context import TaskRuntimeContext
from plombery.utils import run_all_coroutines
from plombery.websocket import sio
from plombery.database.models import PipelineRun
from plombery.database.repository import (
    create_pipeline_run,
    create_task_run_output,
    get_task_run_by_id_and_run_id,
    get_task_runs_for_pipeline_run,
    update_pipeline_run,
    update_task_run,
)
from plombery.database.schemas import (
    PipelineRunCreate,
    TaskRunOutputCreate,
    TaskRunUpdate,
)
from plombery.pipeline.pipeline import Pipeline, Trigger, Task
from plombery.pipeline.context import pipeline_context, run_context
from plombery.schemas import PipelineRunStatus


def utcnow():
    return datetime.now(tz=timezone.utc)


def _on_pipeline_start(pipeline: Pipeline, trigger: Optional[Trigger] = None):
    input_params = trigger.params.model_dump() if trigger and trigger.params else None

    pipeline_run = create_pipeline_run(
        PipelineRunCreate(
            start_time=utcnow(),
            pipeline_id=pipeline.id,
            trigger_id=trigger.id if trigger else MANUAL_TRIGGER_ID,
            status=PipelineRunStatus.RUNNING,
            input_params=input_params,
            reason="scheduled",
        )
    )

    _send_pipeline_event(pipeline, pipeline_run)

    return pipeline_run


def on_pipeline_status_changed(
    pipeline: Pipeline, pipeline_run: PipelineRun, status: PipelineRunStatus
):
    update_pipeline_run(pipeline_run, utcnow(), status)

    _send_pipeline_event(pipeline, pipeline_run)

    if status.is_finished():
        close_logger(pipeline, pipeline_run)

    return pipeline_run


def _send_pipeline_event(pipeline: Pipeline, pipeline_run: PipelineRun):
    notify_coro = notification_manager.notify(pipeline, pipeline_run)

    run_payload = dict(
        id=pipeline_run.id,
        status=pipeline_run.status,
        start_time=(
            pipeline_run.start_time.isoformat() if pipeline_run.start_time else None
        ),
        duration=pipeline_run.duration,
    )

    emit_coro = sio.emit(
        "run-update",
        dict(
            run=run_payload,
            pipeline=pipeline_run.pipeline_id,
            trigger=pipeline_run.trigger_id,
        ),
    )

    run_all_coroutines([notify_coro, emit_coro])


async def execute_task_instance(
    pipeline: Pipeline,
    task: Task,
    pipeline_run: PipelineRun,
):
    """
    Executes a single task instance within a running pipeline.
    This function is called directly by the Orchestrator.
    """
    logger = get_logger()

    task_run = get_task_run_by_id_and_run_id(task.id, pipeline_run.id)
    if not task_run:
        raise ValueError(f"TaskRun {pipeline_run.id}.{task.id} not found")

    logger.info("Executing task %s in pipeline %s", task.id, pipeline.id)

    task_start_time = utcnow()
    task_run_status = PipelineRunStatus.FAILED  # Assume failure until success

    update_task_run(
        task_run.id,
        TaskRunUpdate(
            status=PipelineRunStatus.RUNNING,
        ),
    )

    await sio.emit(
        "run-update",
        dict(
            pipeline=pipeline_run.pipeline_id,
            trigger=pipeline_run.trigger_id,
        ),
    )

    # Prepare arguments using the TaskRun's context/inputs determined by the Orchestrator
    # The Orchestrator should have resolved all upstream tasks' data into task_run.context
    pipeline_params = task_run.context.get("params", None) if task_run.context else None

    task_run_output = None

    try:
        # Pass resolved XCom inputs and pipeline params to the execution wrapper
        task_output = await _execute_task(task, pipeline_run, pipeline_params)

        # Store output and set success status
        if task_output:
            task_run_output = create_task_run_output(
                TaskRunOutputCreate(
                    data=task_output,
                ),
                task_run.id,
            )

        task_run_status = PipelineRunStatus.COMPLETED

    except InvalidDataPath as error:
        logger.error(
            "Can't store the task output as the path is invalid", exc_info=error
        )
    except Exception as e:
        logger.error(str(e), exc_info=e)
    finally:
        task_duration = (utcnow() - task_start_time).total_seconds() * 1000

        # Update the TaskRun record in the database
        update_task_run(
            task_run.id,
            TaskRunUpdate(
                status=task_run_status,
                duration=task_duration,
                end_time=utcnow(),
                task_output_id=task_run_output.id if task_run_output else None,
            ),
        )

        await sio.emit(
            "run-update",
            dict(
                pipeline=pipeline_run.pipeline_id,
                trigger=pipeline_run.trigger_id,
            ),
        )

        # Avoid circular import
        from plombery.orchestrator import orchestrator

        await orchestrator.handle_task_completion(pipeline_run, task.id)


async def run(
    pipeline: Pipeline,
    trigger: Optional[Trigger] = None,
    params: Optional[Dict[str, Any]] = None,
    pipeline_run: Optional[PipelineRun] = None,
):
    """
    This is the function that actually runs the pipeline, running all its tasks.

    `pipeline_run` is typically supplied when the pipeline is run manually,
        in this case one wants to know immediately the run_id to follow
        the execution of the pipeline.
    """

    if pipeline_run:
        on_pipeline_status_changed(pipeline, pipeline_run, PipelineRunStatus.RUNNING)
    else:
        pipeline_run = _on_pipeline_start(pipeline, trigger)

    pipeline_token = pipeline_context.set(pipeline)
    run_token = run_context.set(pipeline_run)

    logger = get_logger()

    logger.info(
        "Executing pipeline `%s` #%d via trigger `%s`",
        pipeline.id,
        pipeline_run.id,
        trigger.id if trigger else MANUAL_TRIGGER_ID,
    )

    from plombery.orchestrator import orchestrator  # Avoid circular import

    orchestrator.start_pipeline_tasks(pipeline, pipeline_run, params)

    pipeline_context.reset(pipeline_token)
    run_context.reset(run_token)


@dataclass
class TaskFunctionSignature:
    has_positional_args: bool = False
    has_params_arg: bool = False
    has_context_arg: bool = False


def check_task_signature(func: Callable) -> TaskFunctionSignature:
    """
    Check if a function signature declares positional args.

    This is meant to be used to check if a task function accepts data inputs from another task.

    The signature of the task run function should be:
    `def task_fn(previous_task_output: Any, params: Model):`

    Where the params argument is the Pipeline input params.
    """

    result = TaskFunctionSignature()

    for name, parameter in inspect.signature(func).parameters.items():
        # Check for positional data inputs (old sequential flow, may be obsolete)
        if (
            parameter.kind == inspect.Parameter.POSITIONAL_ONLY
            or parameter.kind == inspect.Parameter.VAR_POSITIONAL
        ) and name != "params":
            result.has_positional_args = True

        # Check for keyword arguments
        if (
            parameter.VAR_KEYWORD
            or parameter.KEYWORD_ONLY
            or parameter.POSITIONAL_OR_KEYWORD
        ):

            if name == "params":
                result.has_params_arg = True
            elif name == "context":  # Detect the new context injection point
                result.has_context_arg = True

    return result


async def _execute_task(
    task: Task,
    pipeline_run: PipelineRun,
    pipeline_params: Optional[BaseModel] = None,
):
    result = check_task_signature(task.run)

    kwargs = {}

    if pipeline_params and result.has_params_arg:
        kwargs["params"] = pipeline_params

    # 1. Load ONLY TaskRun METADATA for all upstream dependencies
    if result.has_context_arg:
        # Load the TaskRun MODELs for all upstream dependencies
        upstream_runs_metadata = get_task_runs_for_pipeline_run(
            pipeline_run.id, task.upstream_task_ids
        )

        # Build the map of task_id -> TaskRun model instance
        metadata_map = {run.task_id: run for run in upstream_runs_metadata}

        # 2. Instantiate the Context Provider
        runtime_context = TaskRuntimeContext(pipeline_run.id, metadata_map)
        kwargs["context"] = runtime_context

    task_output = await task.run(**kwargs)
    return task_output

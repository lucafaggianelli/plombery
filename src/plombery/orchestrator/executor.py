import asyncio
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Dict, Optional
import inspect

from pydantic import BaseModel

from plombery.constants import MANUAL_TRIGGER_ID
from plombery.exceptions import InvalidDataPath
from plombery.logger import close_logger, get_logger
from plombery.notifications import notification_manager
from plombery.orchestrator.context import Context
from plombery.utils import run_all_coroutines, utcnow
from plombery.websocket import sio
from plombery.database.models import PipelineRun, TaskRun
from plombery.database.repository import (
    create_pipeline_run,
    create_task_run_output,
    get_task_run_by_id,
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
from plombery.pipeline.context import (
    pipeline_context,
    task_context,
    run_context,
    task_run_context,
)
from plombery.schemas import PipelineRunStatus


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
    pipeline: Pipeline, task: Task, pipeline_run: PipelineRun, task_run_id: str
):
    """
    Executes a single task instance within a running pipeline.
    This function is called directly by the Orchestrator.
    """
    logger = get_logger()

    task_run = get_task_run_by_id(task_run_id)
    if not task_run:
        raise ValueError(f"TaskRun {task_run_id} not found")

    logger.info(
        "Executing task %s %sin pipeline %s (id=%s)",
        task.id,
        "" if task_run.map_index is None else f"index {task_run.map_index} ",
        pipeline.id,
        task_run.id,
    )

    update_task_run(
        task_run.id,
        TaskRunUpdate(
            status=PipelineRunStatus.RUNNING,
        ),
    )

    await sio.emit(
        "run-update",
        dict(
            # TODO: remove pipeline_run why we need it? task_run should be sufficient
            pipeline=pipeline_run.pipeline_id,
            trigger=pipeline_run.trigger_id,
        ),
    )

    # Prepare arguments using the TaskRun's context/inputs determined by the Orchestrator
    # The Orchestrator should have resolved all upstream tasks' data into task_run.context
    if task_run.context:
        dict_params = task_run.context.get("params", None)

        if pipeline.params:
            pipeline_params = pipeline.params.model_validate(dict_params)
        else:
            # TODO: This should raise at least a warning
            pipeline_params = dict_params
    else:
        pipeline_params = None

    task_start_time = utcnow()
    task_run_status = PipelineRunStatus.FAILED  # Assume failure until success
    task_run_output = None

    try:
        # Pass resolved XCom inputs and pipeline params to the execution wrapper
        task_output = await _execute_task(task, task_run, pipeline_params)

        # Store output and set success status
        if task_output is not None:
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
        end_time = utcnow()
        task_duration = (end_time - task_start_time).total_seconds() * 1000

        # Update the TaskRun record in the database
        task_run = update_task_run(
            task_run.id,
            TaskRunUpdate(
                status=task_run_status,
                duration=task_duration,
                end_time=end_time,
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

        await orchestrator.handle_task_completion(task_run)


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
    func_params: MappingProxyType[str, inspect.Parameter]
    has_params_arg: bool = False
    context_arg: Optional[str] = None
    input_arg_names: list[str] = field(default_factory=list)


def check_task_signature(func: Callable) -> TaskFunctionSignature:
    """
    Check if a function signature declares positional args.

    This is meant to be used to check if a task function accepts data inputs from another task.

    The signature of the task run function should be:
    `def task_fn(previous_task_output: Any, params: Model):`

    Where the params argument is the Pipeline input params.
    """

    result = TaskFunctionSignature(inspect.signature(func).parameters)

    for name, parameter in result.func_params.items():
        # Check for special arguments
        if name == "params":
            result.has_params_arg = True
        elif name in ["context", "ctx"]:
            result.context_arg = name

        # Check for input data arguments (any other argument)
        else:
            # We treat all non-special arguments as input data to be resolved
            # from upstream tasks, enforcing name-based resolution.
            # We also exclude VAR_KEYWORD and VAR_POSITIONAL (like **kwargs or *args)
            # since they don't map to a single upstream task.
            if parameter.kind not in (
                inspect.Parameter.VAR_KEYWORD,
                inspect.Parameter.VAR_POSITIONAL,
            ):
                result.input_arg_names.append(name)

    return result


async def _execute_task(
    task: Task,
    task_run: TaskRun,
    pipeline_params: Optional[BaseModel] = None,
):
    """Entrypoint to actually run a Task `run` function

    Args:
        task (Task): The task to run
        task_run (TaskRun): The TaskRun object
        pipeline_params (Optional[BaseModel], optional): Input params for the pipeline. Defaults to None.

    Returns:
        Any: The task output to be stored in the TaskRunOutput table, optional.
    """

    token = task_context.set(task)
    tr_token = task_run_context.set(task_run)

    result = check_task_signature(task.run)

    kwargs = {}

    # Load the TaskRuns for all upstream dependencies
    upstream_runs_metadata = get_task_runs_for_pipeline_run(
        task_run.pipeline_run_id, task_ids=task.upstream_task_ids
    )

    # Build the map of task_id -> TaskRun model instance
    metadata_map = {
        (
            f"{run.task_id}.{run.map_index}"
            if run.map_index is not None
            else run.task_id
        ): run
        for run in upstream_runs_metadata
    }
    runtime_context = Context(task_run, metadata_map)

    # Iterate over arguments required by the function signature
    for arg_name in result.input_arg_names:
        # The context handles the mapping logic:
        # - If mapped, resolves to single item if arg_name == map_upstream_id.
        # - Otherwise, resolves to the full output of the upstream task named arg_name.
        input_data = runtime_context.get_output_data(task_id=arg_name)

        arg_annotation = result.func_params[arg_name].annotation

        # If the argument is a Pydantic Model, we parse it
        if issubclass(arg_annotation, BaseModel):
            input_data = arg_annotation.model_validate(input_data)

        kwargs[arg_name] = input_data

    if pipeline_params and result.has_params_arg:
        kwargs["params"] = pipeline_params

    if result.context_arg:
        kwargs[result.context_arg] = runtime_context

    if asyncio.iscoroutinefunction(task.run):
        task_output = await task.run(**kwargs)
    else:
        # Run in thread rather than in event loop to propagate context
        # to sync functions as well.
        #
        # This fixes:
        # https://github.com/lucafaggianelli/plombery/issues/153
        task_output = await asyncio.to_thread(task.run, **kwargs)

    task_context.reset(token)
    task_run_context.reset(tr_token)

    return task_output

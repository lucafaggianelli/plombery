import asyncio
import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel

from plombery.constants import MANUAL_TRIGGER_ID
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
from plombery.exceptions import InvalidDataPath
from plombery.logger import close_logger, get_logger
from plombery.notifications import notification_manager
from plombery.orchestrator.context import Context
from plombery.orchestrator.watchdog import track_running_task
from plombery.pipeline.context import use_context
from plombery.pipeline.pipeline import Pipeline, Task, Trigger
from plombery.pipeline.tasks import OutputOfMarker
from plombery.schemas import PipelineRunStatus
from plombery.secrets import BaseSecrets
from plombery.utils import run_all_coroutines, utcnow
from plombery.websocket import sio


def _on_pipeline_start(
    pipeline: Pipeline,
    trigger: Trigger | None = None,
    input_params: dict[str, Any] | None = None,
):
    pipeline_run = create_pipeline_run(
        PipelineRunCreate(
            start_time=utcnow(),
            pipeline_id=pipeline.id,
            trigger_id=trigger.id if trigger else MANUAL_TRIGGER_ID,
            status=PipelineRunStatus.RUNNING,
            input_params=input_params,
            reason="scheduled",
            pipeline_version=pipeline.get_version(),
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
        close_logger(pipeline_run)

    return pipeline_run


def build_run_update_payload(pipeline_run: PipelineRun) -> dict[str, Any]:
    """The payload of a `run-update` event.

    Every emitter has to send the same shape: the frontend reads `run` to
    refresh the runs list, and an event without it leaves the list showing a
    run as still going long after it finished.
    """

    return {
        "run": {
            "id": pipeline_run.id,
            "status": pipeline_run.status,
            "start_time": (
                pipeline_run.start_time.isoformat() if pipeline_run.start_time else None
            ),
            "duration": pipeline_run.duration,
        },
        "pipeline": pipeline_run.pipeline_id,
        "trigger": pipeline_run.trigger_id,
    }


def _send_pipeline_event(pipeline: Pipeline, pipeline_run: PipelineRun):
    notify_coro = notification_manager.notify(pipeline, pipeline_run)

    emit_coro = sio.emit("run-update", build_run_update_payload(pipeline_run))

    run_all_coroutines([notify_coro, emit_coro])


async def execute_task_instance(
    pipeline: Pipeline, task: Task, pipeline_run: PipelineRun, task_run_id: str
):
    """
    Executes a single task instance within a running pipeline.
    This function is called directly by the Orchestrator.
    """
    task_run = get_task_run_by_id(task_run_id)

    # The contexts are bound around the whole execution, and not just around the
    # call to the task function: `get_logger` reads out of them the task a log
    # line belongs to, so anything logged outside them — a failing task, most of
    # all — would be labelled with no task at all, with no way to tell which one
    # produced it. They are bound explicitly rather than inherited from the
    # context that scheduled this instance, which is the one of the task that
    # completed before it, or of the pipeline for an entry point.
    with use_context(pipeline=pipeline, run=pipeline_run, task=task, task_run=task_run):
        logger = get_logger()

        if not task_run:
            # Without the row there is no way to advance the DAG from here, so
            # fail the run rather than leave it RUNNING forever.
            logger.error("TaskRun %s not found", task_run_id)
            on_pipeline_status_changed(pipeline, pipeline_run, PipelineRunStatus.FAILED)
            return

        task_start_time = utcnow()
        task_run_status = PipelineRunStatus.FAILED  # Assume failure until success
        task_run_output = None

        # Everything that can raise belongs inside the try: an exception escaping
        # this function skips the `finally` that advances the DAG, and the run would
        # hang. Resolving the input params is the likeliest offender, since invalid
        # params raise a Pydantic ValidationError.
        try:
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

            await sio.emit("run-update", build_run_update_payload(pipeline_run))

            # Prepare arguments using the TaskRun's context/inputs determined by the Orchestrator
            # The Orchestrator should have resolved all upstream tasks' data into task_run.context
            if task_run.context:
                dict_params = task_run.context.get("params", None)

                if pipeline.params:
                    # Pydantic models always need a dict input, so provide one as default if the dict_params is None
                    # typically because the pipeline was triggered by a trigger with no params
                    pipeline_params = pipeline.params.model_validate(dict_params or {})
                else:
                    # TODO: This should raise at least a warning
                    pipeline_params = dict_params
            else:
                pipeline_params = None

            # Pass resolved XCom inputs and pipeline params to the execution wrapper
            with track_running_task(task_run.id, task.id):
                task_output = await _execute_task(
                    pipeline, task, task_run, pipeline_params
                )

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

            await sio.emit("run-update", build_run_update_payload(pipeline_run))

            # The `orchestrator` singleton is created at the end of
            # orchestrator/__init__.py, which imports this module on the way there,
            # so it can't be imported at the top — only once, lazily, at call time.
            from plombery.orchestrator import orchestrator

            try:
                await orchestrator.handle_task_completion(task_run)
            except Exception as error:
                # Orchestration itself failed (bad fan-out input, missing task, ...).
                # Without this guard the exception escapes into the executor and the
                # pipeline run stays RUNNING forever, as nothing else will ever
                # advance the DAG.
                logger.error(
                    "Cannot schedule the tasks downstream of %s",
                    task.id,
                    exc_info=error,
                )
                on_pipeline_status_changed(
                    pipeline, pipeline_run, PipelineRunStatus.FAILED
                )


async def run(
    pipeline: Pipeline,
    trigger: Trigger | None = None,
    params: dict[str, Any] | None = None,
    pipeline_run: PipelineRun | None = None,
):
    """
    This is the function that actually runs the pipeline, running all its tasks.

    `pipeline_run` is typically supplied when the pipeline is run manually,
        in this case one wants to know immediately the run_id to follow
        the execution of the pipeline.
    """

    if pipeline_run:
        # Typically started manually
        on_pipeline_status_changed(pipeline, pipeline_run, PipelineRunStatus.RUNNING)
    else:
        # Typically triggered by a schedule
        pipeline_run = _on_pipeline_start(
            pipeline, trigger=trigger, input_params=params
        )

    with use_context(pipeline=pipeline, run=pipeline_run):
        logger = get_logger()

        logger.info(
            "Executing pipeline `%s` #%d via trigger `%s`",
            pipeline.id,
            pipeline_run.id,
            trigger.id if trigger else MANUAL_TRIGGER_ID,
        )

        from plombery.orchestrator import orchestrator  # Avoid circular import

        orchestrator.start_pipeline_tasks(pipeline, pipeline_run, params)


@dataclass
class TaskFunctionSignature:
    func_params: MappingProxyType[str, inspect.Parameter]
    has_params_arg: bool = False
    context_arg: str | None = None
    input_arg_names: list[str] = field(default_factory=list)
    # Argument name -> the `BaseSecrets` subclass it's annotated with. These
    # are resolved by injecting a fresh, validated instance, not from upstream
    # task output, and are what lets the required secrets be checked at startup.
    secret_args: dict[str, type[BaseSecrets]] = field(default_factory=dict)


def check_task_signature(func: Callable) -> TaskFunctionSignature:
    """
    Inspect a task function's signature to decide how each argument is supplied.

    An argument is one of:
    - one annotated with `Context`: the runtime `Context` (or, by name,
      `context`/`ctx`)
    - one annotated with a `BaseSecrets` subclass: an injected secrets instance
    - `params`: the pipeline's input params model
    - anything else: input data resolved from an upstream task (by name, or by
      `OutputOf(...)`)

    The injected arguments (`Context`, secrets) are matched by their annotation,
    so they can be called anything; `params` is matched by name, because typing
    it would collide with an upstream output annotated as the same model.
    """

    result = TaskFunctionSignature(inspect.signature(func).parameters)

    for name, parameter in result.func_params.items():
        annotation = parameter.annotation
        is_class = isinstance(annotation, type)

        # An argument annotated with `Context` or with a secrets schema is
        # injected, not resolved from upstream. Matched by annotation, not
        # name, so it can be called anything.
        if is_class and issubclass(annotation, Context):
            result.context_arg = name

        elif is_class and issubclass(annotation, BaseSecrets):
            result.secret_args[name] = annotation

        # `params` and the `context`/`ctx` names stay matched by name, for the
        # common case where the argument isn't annotated.
        elif name == "params":
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
    pipeline: Pipeline,
    task: Task,
    task_run: TaskRun,
    pipeline_params: BaseModel | None = None,
):
    """Entrypoint to actually run a Task `run` function

    Args:
        pipeline (Pipeline): The pipeline `task` belongs to, whose dependency
            graph resolves the task's upstream ids
        task (Task): The task to run
        task_run (TaskRun): The TaskRun object
        pipeline_params (Optional[BaseModel], optional): Input params for the pipeline. Defaults to None.

    Returns:
        Any: The task output to be stored in the TaskRunOutput table, optional.
    """

    result = check_task_signature(task.run)

    kwargs = {}

    upstream_task_ids = pipeline.upstream_of(task.id)

    # Load the TaskRuns for all upstream dependencies
    upstream_runs_metadata = get_task_runs_for_pipeline_run(
        task_run.pipeline_run_id, task_ids=upstream_task_ids
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
        parameter = result.func_params[arg_name]

        # `OutputOf(some_task)` names the upstream task explicitly, so the
        # argument itself is free to have any name. It's still a default
        # value, but not the "plain optional argument" kind handled below.
        if isinstance(parameter.default, OutputOfMarker):
            upstream_task_id = parameter.default.task.id
        # An argument that doesn't name an upstream task but declares a default
        # is a plain optional argument of the function: leave the default alone
        # rather than overwriting it with None.
        elif (
            arg_name not in upstream_task_ids
            and parameter.default is not inspect.Parameter.empty
        ):
            continue
        else:
            upstream_task_id = arg_name

        # The context handles the mapping logic:
        # - If mapped, resolves to single item if arg_name == map_upstream_id.
        # - Otherwise, resolves to the full output of the upstream task named arg_name.
        input_data = runtime_context.get_output_data(task_id=upstream_task_id)

        arg_annotation = parameter.annotation

        # If the argument is a Pydantic Model, we parse it. `isinstance(..., type)`
        # guards against generic annotations such as `List[int]` or `Optional[str]`,
        # which are not classes and would make `issubclass` raise a TypeError.
        if isinstance(arg_annotation, type) and issubclass(arg_annotation, BaseModel):
            input_data = arg_annotation.model_validate(input_data or {})

        kwargs[arg_name] = input_data

    if pipeline_params and result.has_params_arg:
        kwargs["params"] = pipeline_params

    if result.context_arg:
        kwargs[result.context_arg] = runtime_context

    # Inject a fresh, validated instance of each declared secrets schema.
    # Fresh, so rotating a secret takes effect without a restart; validated,
    # because constructing the class reads and checks the environment. A
    # missing secret raises here, but startup analysis has already surfaced it.
    for arg_name, secrets_cls in result.secret_args.items():
        kwargs[arg_name] = secrets_cls()

    if inspect.iscoroutinefunction(task.run):
        task_output = await task.run(**kwargs)
    else:
        # Run in thread rather than in event loop to propagate context
        # to sync functions as well.
        #
        # This fixes:
        # https://github.com/lucafaggianelli/plombery/issues/153
        task_output = await asyncio.to_thread(task.run, **kwargs)

    return task_output

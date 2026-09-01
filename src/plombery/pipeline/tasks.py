from enum import Enum
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
    overload,
)

from pydantic import BaseModel, PrivateAttr, model_validator, Field

from ._utils import prettify_name


class MappingMode(str, Enum):
    """Defines how a task handles list output from its upstream dependencies."""

    FAN_OUT = "fan_out"

    CHAINED_FAN_OUT = "chained_fan_out"


R = TypeVar("R")  # The return type of the user's function
P = ParamSpec("P")  # The parameters of the task


class OutputOfMarker(Generic[R]):
    """Runtime marker left behind by `OutputOf`, in place of an actual default.

    The executor reads `.task` off it to resolve the argument's value from
    that specific upstream task's output, and `Pipeline` validation reads it
    to check that the dependency was also declared with `>>`/`<<`. It's never
    used as a value itself.
    """

    __slots__ = ("task",)

    def __init__(self, task: "Task") -> None:
        self.task = task

    def __repr__(self) -> str:
        return f"OutputOf({self.task.id})"


def OutputOf(task: "Task[P, R]") -> R:
    """Bind a task argument to a specific upstream task's output.

    Use it when the argument name shouldn't have to match the upstream task's
    id, which is otherwise how an argument is resolved:

        @task
        def fetch_data() -> list[dict]: ...

        @task
        def process(data: list[dict] = OutputOf(fetch_data)): ...

    Declared to statically return `R`, the return type of `task`, so a type
    checker flags a mismatch between the argument's own annotation and what
    `task` actually returns. At runtime this returns a marker instead, read by
    the executor rather than ever being the parameter's real default value.

    This only binds the data: the dependency itself still has to be declared
    with `>>` or `<<`, and `Pipeline` rejects a pipeline where the two disagree.
    """

    return OutputOfMarker(task)  # type: ignore[return-value]


class Task(BaseModel, Generic[P, R]):
    id: str
    run: Callable = Field(
        exclude=True,
    )
    name: Optional[str] = None
    description: Optional[str] = None

    # Purely a display/serialization cache — the DAG viewer reads these off
    # the API response. A `Pipeline` overwrites them, scoped to itself,
    # whenever it adopts this task; nothing else should ever read them, since
    # after a second pipeline reuses this object they only reflect whichever
    # pipeline touched it last.
    downstream_task_ids: set["str"] = set()
    upstream_task_ids: set[str] = set()

    # Edges recorded by `>>`/`<<` before any `Pipeline` exists to claim them
    # (the flat `register_pipeline` form, where wiring happens before the
    # `Pipeline(tasks=[...])` call). Private: a `Pipeline` drains these once,
    # the first time it adopts this task, and never again — which is what
    # keeps the task safe to wire into a second pipeline afterwards.
    _pending_upstream_ids: set[str] = PrivateAttr(default_factory=set)
    _pending_downstream_ids: set[str] = PrivateAttr(default_factory=set)

    mapping_mode: Optional[MappingMode] = None
    # The Task ID that provides the list/map item. Required for all non-None modes.
    map_upstream_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def generate_default_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("name", None):
                data["name"] = prettify_name(data["id"]).title()

        return data

    def validate_mapping(self, upstream_ids: set[str]) -> None:
        """Checks the mapping configuration against `upstream_ids`, the ids
        of this task's dependencies *in one specific pipeline* — passed in
        rather than read off this object, since the same task can be wired
        differently in another pipeline.
        """

        # Check for required map_upstream_id when mapping_mode is active
        if self.mapping_mode and not self.map_upstream_id:
            raise ValueError(
                f"Task {self.id} with mapping mode must specify 'map_upstream_id'."
            )

        # Ensure map_upstream_id is actually an upstream dependency
        if self.map_upstream_id and self.map_upstream_id not in upstream_ids:
            raise ValueError(
                f"Task {self.id} 'map_upstream_id' must be in 'upstream_task_ids'."
            )

    @model_validator(mode="after")
    def add_task_to_pipeline(self):
        from .context import pipeline_context

        pipeline = pipeline_context.get(None)
        if pipeline:
            pipeline.tasks.append(self)

        return self

    def __rshift__(self, other):
        # Handle single task dependency: self >> other
        if isinstance(other, Task):
            self._set_downstream(other)
            return other

        # Handle list/tuple of tasks (e.g., self >> [task_a, task_b])
        elif isinstance(other, (list, tuple)):
            for task in other:
                if not isinstance(task, Task):
                    raise TypeError(f"List item must be a Task, got {type(task)}")
                self._set_downstream(task)
            return other[
                -1
            ]  # Convention: return the rightmost object (or the list itself)

        else:
            raise TypeError(f"Unsupported operand type for >>: {type(other)}")

    def _set_downstream(self, task: "Task"):
        # A runs before B: A is UPSTREAM of B; B is DOWNSTREAM of A
        from .context import pipeline_context

        pipeline = pipeline_context.get(None)

        if pipeline:
            # Record the edge on the pipeline, never on the tasks themselves:
            # a `Task` is a reusable definition, and mutating it here would
            # leak this pipeline's edges into whichever other pipeline reuses
            # the same object. `add_task` also mirrors the edge back onto
            # `upstream_task_ids`/`downstream_task_ids` for display (the
            # DAG viewer reads them from the API), scoped to this pipeline.
            pipeline.add_edge(self.id, task.id)
            pipeline.add_task(self)
            pipeline.add_task(task)
        else:
            # No pipeline exists yet: this is the flat `register_pipeline`
            # form, where `>>` runs before any `Pipeline` is constructed.
            # Stash the edge on the pending, private fields; `Pipeline.
            # add_task` drains them once it adopts the task, so the objects
            # are safe to wire into a different pipeline afterwards.
            self._pending_downstream_ids.add(task.id)
            task._pending_upstream_ids.add(self.id)

    # Optional: Implement the reverse operator << (left shift) via __lshift__
    def __lshift__(self, other):
        # other << self is the same as other >> self
        # This means 'other' is downstream of 'self'
        if isinstance(other, Task):
            other._set_downstream(self)
            return self

        elif isinstance(other, (list, tuple)):
            for task in other:
                if not isinstance(task, Task):
                    raise TypeError(f"List item must be a Task, got {type(task)}")
                task._set_downstream(self)
            return other[
                0
            ]  # Convention: return the leftmost object (or the list itself)
        else:
            raise TypeError(f"Unsupported operand type for <<: {type(other)}")


@overload
def task(
    _func: Callable[P, R],
) -> Task[P, R]: ...


@overload
def task(
    *,
    id: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    mapping_mode: Optional[MappingMode] = None,
    map_upstream_id: Optional[str] = None,
) -> Callable[[Callable[P, R]], Task[P, R]]: ...


def task(
    _func: Optional[Callable[P, R]] = None,
    *,
    id: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    mapping_mode: Optional[MappingMode] = None,
    map_upstream_id: Optional[str] = None,
) -> Union[Task[P, R], Callable[[Callable[P, R]], Task[P, R]]]:
    def decorator(func: Callable[P, R]) -> Task[P, R]:
        task_id = id or func.__name__
        task_description = description or func.__doc__

        return Task[P, R](
            id=task_id,
            run=func,
            name=name,
            description=task_description,
            mapping_mode=mapping_mode,
            map_upstream_id=map_upstream_id,
        )

    if _func:
        return decorator(_func)
    else:
        return decorator

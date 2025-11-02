from enum import Enum
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
    overload,
)

# TODO: Remove python3.9
from typing_extensions import ParamSpec

from pydantic import BaseModel, model_validator, Field

from ._utils import prettify_name


class MappingMode(str, Enum):
    """Defines how a task handles list output from its upstream dependencies."""

    FAN_OUT = "fan_out"

    CHAINED_FAN_OUT = "chained_fan_out"


R = TypeVar("R")  # The return type of the user's function
P = ParamSpec("P")  # The parameters of the task


class Task(BaseModel, Generic[P, R]):
    id: str
    run: Callable = Field(
        exclude=True,
    )
    name: Optional[str] = None
    description: Optional[str] = None

    downstream_task_ids: set["str"] = set()
    upstream_task_ids: set[str] = set()

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

    def validate_mapping(self):
        # Check for required map_upstream_id when mapping_mode is active
        if self.mapping_mode and not self.map_upstream_id:
            raise ValueError(
                f"Task {self.id} with mapping mode must specify 'map_upstream_id'."
            )

        # Ensure map_upstream_id is actually an upstream dependency
        if self.map_upstream_id and self.map_upstream_id not in self.upstream_task_ids:
            raise ValueError(
                f"Task {self.id} 'map_upstream_id' must be in 'upstream_task_ids'."
            )

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
        self.downstream_task_ids.add(task.id)
        task.upstream_task_ids.add(self.id)

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

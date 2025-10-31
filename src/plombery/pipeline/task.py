from typing import Any, Callable, Optional

from pydantic import BaseModel, model_validator, Field

from ._utils import prettify_name


class Task(BaseModel):
    id: str
    run: Callable = Field(
        exclude=True,
    )
    name: Optional[str] = None
    description: Optional[str] = None

    # downstream_tasks: list["Task"] = list()
    upstream_task_ids: set[str] = set()

    @model_validator(mode="before")
    @classmethod
    def generate_default_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("name", None):
                data["name"] = prettify_name(data["id"]).title()

        return data

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
        # self.downstream_tasks.append(task)
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

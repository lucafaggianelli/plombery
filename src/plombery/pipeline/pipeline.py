from typing import Any, Optional, Type

from pydantic import BaseModel, Field, model_validator

from plombery.orchestrator.dag import is_graph_acyclic
from .tasks import Task
from .trigger import Trigger
from ._utils import prettify_name


class Pipeline(BaseModel):
    id: str
    tasks: list[Task]
    name: Optional[str]
    description: Optional[str] = None
    params: Optional[Type[BaseModel]] = Field(exclude=True, default=None)
    triggers: list[Trigger] = Field(default_factory=list)

    class Config:
        validate_assignment = True

    @model_validator(mode="before")
    @classmethod
    def generate_default_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("name", None):
                data["name"] = prettify_name(data["id"]).title()

            if not data.get("description", None):
                data["description"] = cls.__doc__

        return data

    @model_validator(mode="after")
    def validate_dag_dependencies(self):
        """
        Validates the dependencies to ensure all upstream tasks exist
        and that no cyclic dependencies are present.
        """

        task_id_set = {task.id for task in self.tasks}

        # Check for missing upstream tasks
        for task in self.tasks:
            for upstream_id in task.upstream_task_ids:
                if upstream_id not in task_id_set:
                    raise ValueError(
                        f"Task '{task.id}' depends on non-existent task '{upstream_id}'."
                    )

        # Check for cycles
        if not is_graph_acyclic(self.tasks):
            raise ValueError(
                f"Pipeline '{self.id}' contains a cyclic dependency and cannot run."
            )

        for task in self.tasks:
            task.validate_mapping()

        return self

    def get_task_by_id(self, task_id: str):
        for task in self.tasks:
            if task.id == task_id:
                return task

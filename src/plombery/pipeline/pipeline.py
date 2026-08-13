import hashlib
import json
from typing import Any, Optional, Type

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from plombery.orchestrator.dag import is_graph_acyclic
from .tasks import Task
from .trigger import Trigger
from ._utils import prettify_name


class Pipeline(BaseModel):
    id: str
    tasks: list[Task] = Field(default_factory=list)
    name: Optional[str] = None
    description: Optional[str] = None
    params: Optional[Type[BaseModel]] = Field(exclude=True, default=None)
    triggers: list[Trigger] = Field(default_factory=list)
    fail_fast: bool = Field(
        default=True,
        description=(
            "Stop scheduling new work as soon as a task fails. Turn it off "
            "when the branches of a fan-out are independent of each other, "
            "such as one branch per input file: the branches that succeeded "
            "then run all the way to the end, and only the failed branch is "
            "cancelled. Either way the run finishes as failed."
        ),
    )
    version: Optional[str] = Field(
        default=None,
        description=(
            "Identifies the definition this pipeline was run with, so that a "
            "run made before a change can be told from one made after. Set it "
            "to a git commit SHA, a release number or anything meaningful for "
            "the project; when left empty a hash of the graph is computed, "
            "which changes whenever tasks or dependencies do."
        ),
    )

    model_config = ConfigDict(validate_assignment=True)

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

    def __enter__(self):
        from .context import pipeline_context

        self._p_token = pipeline_context.set(self)
        return self

    def __exit__(self, type, value, traceback):
        from .context import pipeline_context

        pipeline_context.reset(self._p_token)

        if not is_graph_acyclic(self.tasks):
            raise ValueError(
                f"Pipeline '{self.id}' contains a cyclic dependency and cannot run."
            )

    @field_serializer("version")
    def _serialize_version(self, version: Optional[str]) -> str:
        """Always expose the effective version, computing it when unset.

        The stored field stays empty so that it is clear the project didn't
        pick a version itself, but a client comparing a run against the current
        definition needs the value that was actually recorded.
        """

        return version or self.get_version()

    def get_version(self) -> str:
        """The version this pipeline is currently running.

        An explicit `version` wins, so a project can record its own git SHA or
        release number. Otherwise a short hash of the graph is derived from the
        task IDs, their dependencies and their mapping: it changes exactly when
        the shape of the pipeline does, which is what makes it possible to tell
        whether two runs executed the same definition.
        """

        if self.version:
            return self.version

        shape = [
            (
                task.id,
                sorted(task.upstream_task_ids),
                task.mapping_mode.value if task.mapping_mode else None,
                task.map_upstream_id,
            )
            for task in sorted(self.tasks, key=lambda task: task.id)
        ]

        digest = hashlib.sha256(json.dumps(shape, default=str).encode())

        return digest.hexdigest()[:12]

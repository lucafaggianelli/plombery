import inspect
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    computed_field,
    field_serializer,
    model_validator,
)

from plombery.config import settings
from plombery.orchestrator.dag import is_graph_acyclic
from plombery.schemas import PipelineIssue
from .tasks import OutputOfMarker, Task
from .trigger import Trigger
from ._utils import prettify_name
from .versioning import get_version_from_git


class Pipeline(BaseModel):
    id: str
    tasks: list[Task] = Field(default_factory=list)
    name: str | None = None
    description: str | None = None
    params: type[BaseModel] | None = Field(exclude=True, default=None)
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
    version: str | None = Field(
        default=None,
        description=(
            "Identifies the definition this pipeline was run with, so that a "
            "run made before a change can be told from one made after. Set it "
            "to a release number or anything meaningful for the project; when "
            "left empty it is taken from the `pipeline_version` setting, or "
            "from the git repository the pipeline is defined in."
        ),
    )
    auto_register: bool = Field(
        default=True,
        exclude=True,
        description=(
            "Register the pipeline with Plombery automatically when the "
            "`with Pipeline()` block ends. Set it to False to build a pipeline "
            "without registering it, for a test or to register it later."
        ),
    )
    issues: list[PipelineIssue] = Field(
        default_factory=list,
        description=(
            "Problems found when the pipeline was checked at startup, such as a "
            "required secret that isn't set. Computed once at startup and stored "
            "here, so it doesn't have to be recomputed on every request."
        ),
    )

    model_config = ConfigDict(validate_assignment=True)

    @computed_field
    @property
    def runnable(self) -> bool:
        """Whether the pipeline can run, i.e. has no error-level issue."""

        return not any(issue.level == "error" for issue in self.issues)

    # The dependency graph, keyed by task id. Deliberately not on `Task`
    # itself: a `Task` is a reusable definition, and if two pipelines wired it
    # differently, storing the edges on the shared object would make one
    # pipeline's dependencies leak into the other's scheduling decisions.
    # Populated by `add_edge` and read through `upstream_of`/`downstream_of`.
    _upstream: dict[str, set[str]] = PrivateAttr(default_factory=dict)
    _downstream: dict[str, set[str]] = PrivateAttr(default_factory=dict)

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
        """Validates the dependencies, run at construction time.

        This only catches what's wrong with the tasks passed to the
        constructor directly (the flat `register_pipeline` form): the context
        manager form adds tasks to `self.tasks` *after* construction, by
        mutating the list in place, which `validate_assignment` doesn't see.
        `__exit__` calls `_check_dag` again once every task is in, so both
        forms end up fully validated either way.
        """

        self._check_dag()

        return self

    def _check_dag(self) -> None:
        """Validates the dependencies to ensure all upstream tasks exist,
        that every `OutputOf(...)` binding has a matching declared dependency,
        that no cyclic dependencies are present, and that the mapping
        configuration of every task is consistent.
        """

        # The flat `register_pipeline(tasks=[...])` form assigns `self.tasks`
        # directly, bypassing `add_task`, so any edge still pending on the
        # objects (from `>>` used before this `Pipeline` existed) hasn't been
        # adopted yet. Do that first, for every task, so the checks below see
        # the whole graph regardless of which form built it.
        for task in self.tasks:
            self._absorb_pending_edges(task)

        task_id_set = {task.id for task in self.tasks}

        # Check for missing upstream tasks
        for task in self.tasks:
            for upstream_id in self.upstream_of(task.id):
                if upstream_id not in task_id_set:
                    raise ValueError(
                        f"Task '{task.id}' depends on non-existent task '{upstream_id}'."
                    )

        # `OutputOf(...)` only binds data, it never creates a dependency by
        # itself: the graph is declared exclusively with `>>`/`<<`, on purpose,
        # so that the topology stays reviewable and doesn't change as a side
        # effect of a signature refactor. This catches the two disagreeing.
        for task in self.tasks:
            for name, parameter in inspect.signature(task.run).parameters.items():
                if not isinstance(parameter.default, OutputOfMarker):
                    continue

                referenced_id = parameter.default.task.id

                if referenced_id not in self.upstream_of(task.id):
                    raise ValueError(
                        f"Task '{task.id}' reads OutputOf({referenced_id}) on "
                        f"argument '{name}', but there's no declared dependency: "
                        f"add `{referenced_id} >> {task.id}` (or `<<`)."
                    )

        # Check for cycles
        if not is_graph_acyclic(task_id_set, self._upstream):
            raise ValueError(
                f"Pipeline '{self.id}' contains a cyclic dependency and cannot run."
            )

        for task in self.tasks:
            task.validate_mapping(self.upstream_of(task.id))

    def get_task_by_id(self, task_id: str):
        for task in self.tasks:
            if task.id == task_id:
                return task

    def add_edge(self, upstream_id: str, downstream_id: str) -> None:
        """Record that `downstream_id` depends on `upstream_id`, in this
        pipeline only.

        This is where `>>`/`<<` land when used inside a `with Pipeline()`
        block: never on the `Task` objects themselves, so the same task can
        be wired differently in another pipeline without either leaking into
        the other's scheduling decisions.
        """

        self._downstream.setdefault(upstream_id, set()).add(downstream_id)
        self._upstream.setdefault(downstream_id, set()).add(upstream_id)

    def upstream_of(self, task_id: str) -> set[str]:
        """The ids of the tasks that must complete before `task_id` runs, in
        this pipeline."""

        return self._upstream.get(task_id, set())

    def downstream_of(self, task_id: str) -> set[str]:
        """The ids of the tasks that depend on `task_id`, in this pipeline."""

        return self._downstream.get(task_id, set())

    def add_task(self, task: Task) -> None:
        """Add a task to this pipeline, unless it's already part of it.

        Idempotent so that wiring the same task more than once, such as the
        join of a diamond, doesn't add it twice.
        """

        if self.get_task_by_id(task.id) is None:
            self.tasks.append(task)

        self._absorb_pending_edges(task)

    def _absorb_pending_edges(self, task: Task) -> None:
        """Adopt any edge `>>`/`<<` recorded on `task` before it had a
        pipeline to belong to (the flat `register_pipeline` form, where `>>`
        runs before any `Pipeline` exists), then resync the task's own
        `upstream_task_ids`/`downstream_task_ids` to this pipeline's view, for
        display and API serialization.

        Draining the *pending* edges (never the display fields — those are
        never read here, only written) is what keeps a `Task` safe to reuse:
        wiring the same object into a second pipeline starts from nothing,
        instead of the second pipeline re-adopting whatever the first one
        already resynced onto the display fields. Safe to call more than once
        for the same task: once drained, there's nothing left to adopt, and
        adding an edge that's already recorded is a no-op.
        """

        for upstream_id in task._pending_upstream_ids:
            self.add_edge(upstream_id, task.id)
        for downstream_id in task._pending_downstream_ids:
            self.add_edge(task.id, downstream_id)

        task._pending_upstream_ids = set()
        task._pending_downstream_ids = set()

        task.upstream_task_ids = self.upstream_of(task.id)
        task.downstream_task_ids = self.downstream_of(task.id)

    def __enter__(self):
        from .context import pipeline_context

        self._p_token = pipeline_context.set(self)
        return self

    def __exit__(self, type, value, traceback):
        from .context import pipeline_context

        pipeline_context.reset(self._p_token)

        # Leave a failing block alone: don't validate or register a pipeline
        # whose definition raised half-way through.
        if type is not None:
            return

        # Tasks are added to `self.tasks` throughout the block, after the
        # model validator already ran once on an empty list at construction:
        # re-run the full check now that every task is in.
        self._check_dag()

        # Register the pipeline as soon as its block ends, so importing the
        # module that defines it is enough — no separate `register_pipeline`
        # call. The registry lives on the orchestrator; import it lazily to
        # avoid a circular import at module load.
        if self.auto_register:
            from plombery.orchestrator import orchestrator

            orchestrator.register_pipeline(self)

    @field_serializer("version")
    def _serialize_version(self, version: str | None) -> str | None:
        """Always expose the effective version, resolving it when unset.

        The stored field stays empty so that it is clear the project didn't
        pick a version itself, but a client comparing a run against the current
        definition needs the value that was actually recorded.
        """

        return version or self.get_version()

    def get_version(self) -> str | None:
        """The version this pipeline is currently running.

        The first of these that yields a value wins:

        1. the pipeline's own `version`, when the project sets one;
        2. the `pipeline_version` setting, which versions every pipeline of a
           deployment at once — a container image usually ships without the
           git history that produced it, so this is what a deployment sets,
           from its build;
        3. the revision of the git repository the pipeline is defined in, as
           `git describe --tags --always --dirty` reports it.

        `None` when none of them answers: nothing else identifies the code a
        run executed. The shape of the graph doesn't, in particular — a task
        can be rewritten from top to bottom without a single edge moving.
        """

        return (
            self.version
            or settings.pipeline_version
            or get_version_from_git(self._get_source_directory())
        )

    def _get_source_directory(self) -> str:
        """The folder to look for a git repository in.

        Pipelines aren't necessarily defined under the working directory, so
        the file defining the first task is a better place to start than
        `Path.cwd()`, which only serves a pipeline with no task at all.
        """

        for task in self.tasks:
            try:
                return str(Path(inspect.getfile(task.run)).parent)
            except TypeError:
                continue

        return str(Path.cwd())

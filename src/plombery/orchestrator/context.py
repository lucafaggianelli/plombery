from typing import Any, Optional
from plombery.database.repository import get_task_run_output_by_id
from plombery.database.models import TaskRun
from plombery.logger import get_logger
from plombery.pipeline.context import task_context
from plombery.pipeline.tasks import MappingMode


class Context:
    """
    Provides runtime information and dependency data access to a running task.
    """

    def __init__(self, _task_run: TaskRun, upstream_task_runs: dict[str, TaskRun]):
        self._task_run = _task_run
        self._upstream_task_runs = upstream_task_runs
        self.logger = get_logger()
        self.task = task_context.get()

    def _read_output(self, task_run: TaskRun) -> Optional[Any]:
        """Reads the stored output of a single task run."""

        if not task_run.task_output_id:
            return None

        output_record = get_task_run_output_by_id(task_run.task_output_id)

        # Should not happen if task_output_id is set
        return output_record.data if output_record else None

    def get_output_data(self, task_id: str) -> Optional[Any]:
        """
        Imperatively retrieves the full TaskRunOutput data (XCom) for a specified
        upstream task, performing a database lookup only upon call.
        """
        if (
            self._task_run.map_index is not None
            # if it's a Chained Fan Out the upstream is returning a
            # primitive value and not an array, si we retrieve the value of
            # the corresponding task + map_index
            and self.task.mapping_mode == MappingMode.CHAINED_FAN_OUT
        ):
            task_full_id = f"{task_id}.{self._task_run.map_index}"
        else:
            task_full_id = task_id

        target_task_run = self._upstream_task_runs.get(task_full_id)

        if target_task_run is None:
            # No run is registered under the plain task ID, which means the
            # upstream task was mapped (its runs are keyed `task_id.map_index`)
            # while this task is not: this is a fan-in, so gather the output of
            # every instance, ordered by map index.
            mapped_runs = sorted(
                (
                    run
                    for run in self._upstream_task_runs.values()
                    if run.task_id == task_id and run.map_index is not None
                ),
                key=lambda run: run.map_index,
            )

            if mapped_runs:
                return [self._read_output(run) for run in mapped_runs]

            # Task ID not found in upstream dependencies
            return None

        data = self._read_output(target_task_run)

        if (
            data is not None
            and self._task_run.map_index is not None
            # If it's a Fan Out task then the upstream returns a list and we need
            # to get the item at the specific index
            and self.task.mapping_mode == MappingMode.FAN_OUT
        ):
            return data[self._task_run.map_index]

        return data

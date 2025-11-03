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

        if not target_task_run or not target_task_run.task_output_id:
            # Task ID not found in upstream dependencies
            return None

        # Fetch the actual data from the TaskRunOutput table
        output_record = get_task_run_output_by_id(target_task_run.task_output_id)

        if output_record:
            if (
                self._task_run.map_index is not None
                # If it's a Fan Out task then the upstream is return a list and we need
                # to get the item at the specific index
                and self.task.mapping_mode == MappingMode.FAN_OUT
            ):
                return output_record.data[self._task_run.map_index]

            # Return the data stored in the 'data' JSON column
            return output_record.data

        # Should not happen if output_xcom_id is set
        return None

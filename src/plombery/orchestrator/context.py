from typing import Any, Optional
from plombery.database.repository import get_task_run_output_by_id
from plombery.database.models import TaskRun
from plombery.logger import get_logger


class Context:
    """
    Provides runtime information and dependency data access to a running task.
    """

    def __init__(self, _task_run: TaskRun, upstream_task_runs: dict[str, TaskRun]):
        self._task_run = _task_run
        self._upstream_task_runs = upstream_task_runs
        self.logger = get_logger()

    def get_output_data(self, task_id: str) -> Optional[Any]:
        """
        Imperatively retrieves the full TaskRunOutput data (XCom) for a specified
        upstream task, performing a database lookup only upon call.
        """
        target_task_run = self._upstream_task_runs.get(task_id)

        if not target_task_run or not target_task_run.task_output_id:
            # Task ID not found in upstream dependencies
            return None

        # Fetch the actual data from the TaskRunOutput table
        output_record = get_task_run_output_by_id(target_task_run.task_output_id)

        if output_record:
            if self._task_run.map_index is not None:
                return output_record.data[self._task_run.map_index]

            # Return the data stored in the 'data' JSON column
            return output_record.data

        # Should not happen if output_xcom_id is set
        return None

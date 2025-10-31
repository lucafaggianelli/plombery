# plombery/orchestrator/context.py

from typing import Any, Optional
from plombery.database.repository import get_task_run_output_by_id
from plombery.database.models import TaskRun as TaskRunModel


class TaskRuntimeContext:
    """
    Provides runtime information and dependency data access to a running task.
    It LAYS-LOADS the TaskRunOutput data only when get_output_data is called.
    """

    def __init__(
        self, pipeline_run_id: int, upstream_task_run_metadata: dict[str, TaskRunModel]
    ):
        self._pipeline_run_id = pipeline_run_id
        # Stores Task ID -> TaskRun Model instance (only metadata: status, output_xcom_id, etc.)
        self._metadata_map = upstream_task_run_metadata

    def get_output_data(self, task_id: str) -> Optional[Any]:
        """
        Imperatively retrieves the full TaskRunOutput data (XCom) for a specified
        upstream task, performing a database lookup only upon call.
        """
        task_run = self._metadata_map.get(task_id)

        if not task_run or not task_run.task_output_id:
            # Task ID not found in upstream dependencies
            return None

        # Fetch the actual data from the TaskRunOutput table
        output_record = get_task_run_output_by_id(task_run.task_output_id)

        if output_record:
            # Return the data stored in the 'data' JSON column
            return output_record.data

        # Should not happen if output_xcom_id is set
        return None

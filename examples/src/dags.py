from asyncio import sleep
from typing import Dict, Any

from pydantic import BaseModel
from plombery import register_pipeline
from plombery.logger import get_logger
from plombery.orchestrator.context import TaskRuntimeContext
from plombery.pipeline import task


class PipelineInputParams(BaseModel):
    user_id: int
    data_source: str = "default_api"


@task
async def fetch_data(params: PipelineInputParams) -> Dict[str, Any]:
    """Task A: The start node."""
    await sleep(10)
    user_data = {
        "user_list": [101, 102, 103],
        "fetch_timestamp": "2025-10-31T10:00:00Z",
    }
    get_logger().info("Fetch data its me")
    return user_data


@task
def process_list(context: TaskRuntimeContext) -> Dict[str, Any]:
    """Task B: Processes data from Task A."""
    user_list: list[int] | None = context.get_output_data("fetch_data")["user_list"]

    processed_count = len(user_list)
    processed_result = {
        "status": "SUCCESS",
        "total_processed": processed_count,
        "summary_data": [i * 2 for i in user_list],
    }
    get_logger().info("Processed some data")
    return processed_result


@task
async def parallel_task(context: TaskRuntimeContext):
    get_logger().info("Starting parallel task")
    await sleep(10)
    get_logger().info("Done")


@task
def report_success():
    """Task C: The final node."""
    get_logger().info("Final Report Generated.")
    return None


# --- Define Dependencies using the >> Operator ---

# NOTE: Executing this dependency line populates the upstream_task_ids property
# of the task objects within the TaskWrapper instances.
fetch_data >> [process_list, parallel_task] >> report_success
process_list >> report_success

example_dag_pipeline = register_pipeline(
    id="etl_user_processor_decorated",
    name="User Data Processor DAG (Decorated)",
    params=PipelineInputParams,
    tasks=[fetch_data, process_list, report_success, parallel_task],
)

from asyncio import sleep
from typing import Dict, Any

from pydantic import BaseModel
from plombery import register_pipeline, MappingMode, task, Context


class PipelineInputParams(BaseModel):
    user_id: int = 1
    data_source: str = "default_api"


@task()
async def fetch_user_data(ctx: Context) -> Dict[str, Any]:
    """Task A: The start node."""
    await sleep(10)
    user_data = {
        "user_list": [101, 102, 103],
        "fetch_timestamp": "2025-10-31T10:00:00Z",
    }
    ctx.logger.info("Fetch data its me")
    return user_data["user_list"]


@task
async def process_list(fetch_user_data: list[int], context: Context) -> Dict[str, Any]:
    """Task B: Processes data from Task A."""
    await sleep(6)

    processed_count = len(fetch_user_data)
    processed_result = {
        "status": "SUCCESS",
        "total_processed": processed_count,
        "summary_data": [i * 2 for i in fetch_user_data],
    }
    context.logger.info("Processed some data")
    return processed_result


@task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="fetch_user_data")
async def parallel_task(fetch_user_data: int, ctx: Context):
    """Task B: Processes data from Task A one at a time."""
    ctx.logger.info(f"Starting parallel task for user {fetch_user_data}")
    await sleep(5)

    # if fetch_user_data % 2 == 0:
    #     raise ValueError("Decided to fail")

    ctx.logger.info("Done")


@task(mapping_mode=MappingMode.CHAINED_FAN_OUT, map_upstream_id="parallel_task")
async def finalize_user(parallel_task: int, ctx: Context):
    ctx.logger.info(f"Finalizing user {parallel_task}")


@task
def report_success(ctx: Context):
    """Task C: The final node."""
    ctx.logger.info("Final Report Generated.")
    return None


# --- Define Dependencies using the >> Operator ---

# NOTE: Executing this dependency line populates the upstream_task_ids property
# of the task objects within the TaskWrapper instances.
fetch_user_data >> [process_list, parallel_task]
process_list >> report_success
parallel_task >> finalize_user >> report_success


example_dag_pipeline = register_pipeline(
    id="etl_user_processor_decorated",
    name="User Data Processor DAG (Decorated)",
    params=PipelineInputParams,
    tasks=[fetch_user_data, process_list, report_success, parallel_task, finalize_user],
)

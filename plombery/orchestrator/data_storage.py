import json
from pathlib import Path
from typing import Any

from plombery.constants import PIPELINE_RUN_LOGS_FILE


def _get_data_path(pipeline_run_id: int):
    data_path = Path.cwd() / ".data" / "runs" / f"run_{pipeline_run_id}"

    # Create dirs (eq. of mkdir -p)
    data_path.mkdir(parents=True, exist_ok=True)

    return data_path


def store_data(filename: str, content: str, pipeline_run_id: int):
    data_path = _get_data_path(pipeline_run_id)

    with (data_path / filename).open(mode="w") as f:
        f.write(content)


def store_task_output(pipeline_run_id: int, task_id: str, data: Any) -> bool:
    """
    Store a task output as a JSON file

    Args:
        pipeline_run_id (int): the pipeline run ID used to name the folder
            containing the run data
        task_id (str): the id of the task
        data (Any): the actual data to store, if is None or is an empty DataFrame
            it will not be saved

    Returns:
        bool: returns True if the store succeeded, False otherwise
    """
    data_path = _get_data_path(pipeline_run_id)
    output_file = data_path / f"{task_id}.json"

    try:
        import pandas

        if type(data) is pandas.DataFrame:
            if not data.empty:
                data.to_json(output_file, orient="records")
                return True
            else:
                return False
    except ModuleNotFoundError:
        pass

    try:
        if data is None:
            return False

        with output_file.open(mode="w", encoding="utf-8") as f:
            json.dump(data, f, default=str)

        return True
    except Exception as exc:
        print(f"Failed to save task {task_id} output", exc)
        output_file.unlink()
        return False


def get_logs_filename(pipeline_run_id: int):
    return _get_data_path(pipeline_run_id) / PIPELINE_RUN_LOGS_FILE


def read_logs_file(pipeline_run_id: int):
    logs_file = get_logs_filename(pipeline_run_id)

    if not logs_file.exists():
        return

    with logs_file.open(mode="r", encoding="utf-8") as f:
        return f.read().rstrip()


def read_task_run_data(pipeline_run_id: int, task_id: str):
    data_path = _get_data_path(pipeline_run_id)
    file = data_path / f"{task_id}.json"

    if not file.exists():
        return

    with file.open(mode="r", encoding="utf-8") as f:
        return json.load(f)

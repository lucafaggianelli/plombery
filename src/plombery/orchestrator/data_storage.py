import json
from pathlib import Path
from typing import Any, Optional

from plombery.constants import PIPELINE_RUN_LOGS_FILE
from plombery.exceptions import InvalidDataPath
from plombery.config import settings


_base_data_path = (settings.data_path / ".data").absolute()


def _check_is_valid_path(path: Path) -> None:
    """
    Check if a data file path is a valid one and not outside
    the base data path.

    This check is very important in case an attacker try to request
    data files for the run id `../../.env`.

    Raises:
        InvalidDataPath: In case the path is invalid.
    """
    try:
        path.relative_to(_base_data_path)
    except ValueError:
        raise InvalidDataPath(path)


def _get_data_path(pipeline_run_id: int, filename: str) -> Path:
    data_path = _base_data_path / "runs" / f"run_{pipeline_run_id}" / filename

    _check_is_valid_path(data_path)

    # Create all parent directories without raising errors
    # equivalent to mkdir -p
    data_path.parent.mkdir(parents=True, exist_ok=True)

    return data_path


def get_task_run_data_file(pipeline_run_id: int, task_id: str) -> Path:
    """Get the file path of a task run output

    Args:
        pipeline_run_id (int): the run ID
        task_id (str): the task ID

    Returns:
        Path: the file path

    Raises:
        InvalidDataPath: In case the path is invalid.
    """
    return _get_data_path(pipeline_run_id, f"{task_id}.json")


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

    Raises:
        InvalidDataPath: In case the path is invalid.
    """

    output_file_path = get_task_run_data_file(pipeline_run_id, task_id)

    try:
        import pandas

        if type(data) is pandas.DataFrame:
            if not data.empty:
                data.to_json(output_file_path, orient="records")
                return True
            else:
                return False
    except ModuleNotFoundError:
        pass

    try:
        if data is None:
            return False

        with output_file_path.open(mode="w", encoding="utf-8") as output_file:
            json.dump(data, output_file, default=str)

        return True
    except Exception as exc:
        print(f"Failed to save task {task_id} output", exc)
        output_file_path.unlink()
        return False


def get_logs_filename(pipeline_run_id: int) -> Path:
    """Get the logs file path for a given run ID

    Args:
        pipeline_run_id (int): the run ID

    Returns:
        Path: the logs file path

    Raises:
        InvalidDataPath: In case the path is invalid.
    """

    return _get_data_path(pipeline_run_id, PIPELINE_RUN_LOGS_FILE)


def read_logs_file(pipeline_run_id: int) -> Optional[str]:
    """Read a logs file and returns its content or None
    if the file doesn't exist

    Args:
        pipeline_run_id (int): the run ID

    Returns:
        Optional[str]: The logs content in JSONL format

    Raises:
        InvalidDataPath: In case the path is invalid.
    """

    logs_file = get_logs_filename(pipeline_run_id)

    if not logs_file.exists():
        return

    with logs_file.open(mode="r", encoding="utf-8") as f:
        return f.read().rstrip()

import shutil
from pathlib import Path
from typing import List, Optional

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


def get_run_data_dir(pipeline_run_id: int) -> Path:
    """Get the directory holding all the data of a run, without creating it.

    Args:
        pipeline_run_id (int): the run ID

    Returns:
        Path: the run data directory

    Raises:
        InvalidDataPath: In case the path is invalid.
    """

    run_dir = _base_data_path / "runs" / f"run_{pipeline_run_id}"

    _check_is_valid_path(run_dir)

    return run_dir


def delete_run_data(pipeline_run_id: int) -> bool:
    """Delete the whole data directory of a run, logs included.

    Args:
        pipeline_run_id (int): the run ID

    Returns:
        bool: True if there was something to delete
    """

    run_dir = get_run_data_dir(pipeline_run_id)

    if not run_dir.is_dir():
        return False

    shutil.rmtree(run_dir)

    return True


def list_stored_run_ids() -> List[int]:
    """The run IDs that have a data directory on disk.

    Used to find the directories left behind by runs that are no longer in the
    database, for instance because the database was reset.
    """

    runs_dir = _base_data_path / "runs"

    if not runs_dir.is_dir():
        return []

    run_ids = []

    for child in runs_dir.iterdir():
        if not child.is_dir() or not child.name.startswith("run_"):
            continue

        try:
            run_ids.append(int(child.name[len("run_") :]))
        except ValueError:
            # Not a directory Plombery created, leave it alone
            continue

    return run_ids

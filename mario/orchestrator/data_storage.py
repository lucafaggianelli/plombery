import json
from pathlib import Path
from typing import Any

from mario.constants import PIPELINE_RUN_LOGS_FILE


BASE_DATA_PATH = Path.cwd() / ".data"


def get_data_path(pipeline_run_id: int):
    data_path = (
        BASE_DATA_PATH / "runs" / f"run_{pipeline_run_id}"
    )

    # Create dirs (eq. of mkdir -p)
    data_path.mkdir(parents=True, exist_ok=True)

    return data_path


def store_data(filename: str, content: str, pipeline_run_id: int):
    data_path = get_data_path(pipeline_run_id)

    with (data_path / filename).open(mode="w") as f:
        f.write(content)


def store_task_output(pipeline_run_id: int, task_id: str, data: Any):
    data_path = get_data_path(pipeline_run_id)
    output_file = data_path / f"{task_id}.json"

    try:
        import pandas

        if type(data) is pandas.DataFrame:
            data.to_json(output_file, orient="records")
            return
    except ModuleNotFoundError:
        pass

    try:
        import json

        with output_file.open(mode="w", encoding="utf-8") as f:
            json.dump(data, f, default=str)
    except Exception as exc:
        print(f"Failed to save task {task_id} output", exc)
        output_file.unlink()
        pass


def read_logs_file(pipeline_run_id: int):
    data_path = get_data_path(pipeline_run_id)
    file = data_path / PIPELINE_RUN_LOGS_FILE

    if not file.exists():
        return

    with file.open(mode="r", encoding="utf-8") as f:
        return f.read().rstrip()


def read_task_run_data(pipeline_run_id: int, task_id: str):
    data_path = get_data_path(pipeline_run_id)
    file = data_path / f"{task_id}.json"

    if not file.exists():
        return

    with file.open(mode="r", encoding="utf-8") as f:
        return json.load(f)

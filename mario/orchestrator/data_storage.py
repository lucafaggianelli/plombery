import json
from pathlib import Path

from mario.database.models import PipelineRun


BASE_DATA_PATH = Path.cwd() / ".data"


def get_data_path(pipeline_run: PipelineRun):
    data_path = (
        BASE_DATA_PATH / str(pipeline_run.pipeline_id) / f"run_{pipeline_run.id}"
    )

    # Create dirs (eq. of mkdir -p)
    data_path.mkdir(parents=True, exist_ok=True)

    return data_path


def store_data(filename: str, content: str, pipeline_run: PipelineRun):
    data_path = get_data_path(pipeline_run)

    with (data_path / filename).open(mode="w") as f:
        f.write(content)


def read_logs_file(pipeline_run: PipelineRun):
    data_path = get_data_path(pipeline_run)
    file = data_path / "task_run.log"

    if not file.exists():
        return

    with file.open(mode="r", encoding="utf-8") as f:
        return f.read().rstrip()


def read_task_run_data(pipeline_run: PipelineRun, task_id: str):
    data_path = get_data_path(pipeline_run)
    file = data_path / f"{task_id}.json"

    if not file.exists():
        return

    with file.open(mode="r", encoding="utf-8") as f:
        return json.load(f)

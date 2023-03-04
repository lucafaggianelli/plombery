from pathlib import Path

from mario.database.models import PipelineRun


BASE_DATA_PATH = Path.cwd() / ".mario_data"


def get_data_path(pipeline_run: PipelineRun):
    data_path = BASE_DATA_PATH / str(pipeline_run.pipeline_id) / f"run_{pipeline_run.id}"

    # Create dirs (eq. of mkdir -p)
    data_path.mkdir(parents=True, exist_ok=True)

    return data_path


def store_data(filename: str, content: str, pipeline_run: PipelineRun):
    data_path = get_data_path(pipeline_run)

    with (data_path / filename).open(mode='w') as f:
        f.write(content)


def read_data(filename: str, pipeline_run: PipelineRun):
    data_path = get_data_path(pipeline_run)

    with (data_path / filename).open(mode='r') as f:
        return f.read()

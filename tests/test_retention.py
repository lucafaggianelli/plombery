"""Tests for the retention policy."""

from datetime import timedelta

import pytest

from plombery import _Plombery as Plombery
from plombery.config import settings
from plombery.config.model import RetentionSettings
from plombery.database.repository import (
    create_pipeline_run,
    create_task_run,
    create_task_run_output,
    get_pipeline_run,
    list_pipeline_runs,
    update_pipeline_run,
)
from plombery.database.schemas import (
    PipelineRunCreate,
    TaskRunCreate,
    TaskRunOutputCreate,
)
from plombery.orchestrator.data_storage import get_logs_filename, get_run_data_dir
from plombery.retention import apply_retention, delete_orphan_data
from plombery.schemas import PipelineRunStatus
from plombery.utils import utcnow


@pytest.fixture(autouse=True)
def reset_retention_settings():
    original = settings.retention
    yield
    settings.retention = original


def make_run(age_days: float, status=PipelineRunStatus.COMPLETED, with_data=True):
    """Create a finished run that ended `age_days` ago, with logs and output."""

    end_time = utcnow() - timedelta(days=age_days)

    run = create_pipeline_run(
        PipelineRunCreate(
            pipeline_id="a-pipeline",
            trigger_id="_manual",
            status=status,
            start_time=end_time - timedelta(seconds=1),
        )
    )

    task_run = create_task_run(
        TaskRunCreate(
            pipeline_run_id=run.id,
            task_id="a-task",
            status=status,
        )
    )
    create_task_run_output(TaskRunOutputCreate(data={"some": "output"}), task_run.id)

    if with_data:
        # get_logs_filename creates the parent directories
        get_logs_filename(run.id).write_text('{"message": "a log line"}\n')

    if status in (PipelineRunStatus.COMPLETED, PipelineRunStatus.FAILED):
        update_pipeline_run(run, end_time, status)

    return run


@pytest.mark.asyncio
async def test_no_settings_means_nothing_is_deleted(app: Plombery):
    app.start()
    settings.retention = RetentionSettings()

    run = make_run(age_days=900)

    assert not apply_retention()
    assert get_pipeline_run(run.id) is not None
    assert get_run_data_dir(run.id).is_dir()


@pytest.mark.asyncio
async def test_files_threshold_deletes_the_logs_and_keeps_the_run(app: Plombery):
    app.start()
    settings.retention = RetentionSettings(files_days=30)

    old = make_run(age_days=60)
    recent = make_run(age_days=1)

    result = apply_retention()

    assert result.deleted_run_files == 1
    assert result.deleted_runs == 0

    # The history survives, only the files are gone
    assert get_pipeline_run(old.id) is not None
    assert not get_run_data_dir(old.id).is_dir()

    assert get_run_data_dir(recent.id).is_dir()


@pytest.mark.asyncio
async def test_runs_threshold_deletes_the_run_and_its_data(app: Plombery):
    app.start()
    settings.retention = RetentionSettings(runs_days=30)

    old = make_run(age_days=60)
    recent = make_run(age_days=1)

    result = apply_retention()

    assert result.deleted_runs == 1
    assert get_pipeline_run(old.id) is None
    assert not get_run_data_dir(old.id).is_dir()

    assert get_pipeline_run(recent.id) is not None
    assert get_run_data_dir(recent.id).is_dir()


@pytest.mark.asyncio
async def test_both_thresholds_apply_together(app: Plombery):
    app.start()
    settings.retention = RetentionSettings(files_days=10, runs_days=100)

    ancient = make_run(age_days=200)
    middle_aged = make_run(age_days=50)
    recent = make_run(age_days=1)

    apply_retention()

    # Past runs_days: gone entirely
    assert get_pipeline_run(ancient.id) is None

    # Past files_days but not runs_days: kept, without its logs
    assert get_pipeline_run(middle_aged.id) is not None
    assert not get_run_data_dir(middle_aged.id).is_dir()

    # Untouched
    assert get_pipeline_run(recent.id) is not None
    assert get_run_data_dir(recent.id).is_dir()


@pytest.mark.asyncio
async def test_unfinished_runs_are_never_deleted(app: Plombery):
    app.start()
    settings.retention = RetentionSettings(files_days=1, runs_days=1)

    # An old run that never recorded an end time, e.g. the process was killed
    running = make_run(age_days=90, status=PipelineRunStatus.RUNNING)

    apply_retention()

    assert get_pipeline_run(running.id) is not None
    assert get_run_data_dir(running.id).is_dir()


@pytest.mark.asyncio
async def test_deleting_a_run_removes_its_task_runs(app: Plombery):
    app.start()
    settings.retention = RetentionSettings(runs_days=30)

    old = make_run(age_days=60)
    assert get_pipeline_run(old.id).task_runs

    apply_retention()

    assert get_pipeline_run(old.id) is None
    assert all(run.id != old.id for run in list_pipeline_runs())


@pytest.mark.asyncio
async def test_orphan_data_directories_are_deleted(app: Plombery):
    app.start()
    settings.retention = RetentionSettings()

    kept = make_run(age_days=1)

    # A directory whose run is not in the database, as after a database reset
    orphan_id = kept.id + 5_000
    get_logs_filename(orphan_id).write_text("{}\n")
    assert get_run_data_dir(orphan_id).is_dir()

    assert delete_orphan_data() == 1

    assert not get_run_data_dir(orphan_id).is_dir()
    assert get_run_data_dir(kept.id).is_dir()

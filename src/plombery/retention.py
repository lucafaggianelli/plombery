"""Deletion of old runs data, driven by the `retention` settings.

Two independent thresholds, because the two kinds of data age differently:

* `files_days` drops the log files of old runs while keeping the runs
  themselves, so the history and the charts stay intact but the disk doesn't
  grow forever;
* `runs_days` drops the runs entirely, with their task runs, their stored
  outputs and their log files.

Task outputs live in the database rather than on disk, so `runs_days` is the
threshold that reclaims most of the space.

Runs that haven't finished yet are never touched, however old they are.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import delete, select

from plombery._internals.logging import logger
from plombery.config import settings
from plombery.database import models
from plombery.database.repository import session_scope
from plombery.exceptions import InvalidDataPath
from plombery.orchestrator.data_storage import delete_run_data, list_stored_run_ids
from plombery.schemas import FINISHED_STATUS
from plombery.utils import utcnow


@dataclass
class RetentionResult:
    deleted_runs: int = 0
    deleted_run_files: int = 0
    deleted_orphan_files: int = 0

    def __bool__(self) -> bool:
        return bool(
            self.deleted_runs or self.deleted_run_files or self.deleted_orphan_files
        )


def _finished_runs_before(session, cutoff: datetime) -> List[int]:
    """IDs of the runs that finished before the cutoff.

    A run with no end time is either still going or was interrupted before it
    could record one, so it's left alone.
    """

    return list(
        session.execute(
            select(models.PipelineRun.id).where(
                models.PipelineRun.status.in_(FINISHED_STATUS),
                models.PipelineRun.end_time.is_not(None),
                models.PipelineRun.end_time < cutoff,
            )
        )
        .scalars()
        .all()
    )


def _delete_runs(session, run_ids: List[int]) -> None:
    """Delete runs and everything hanging off them.

    The order matters: task runs point at their output, and runs own the task
    runs, so nothing can be removed before the rows referencing it.
    """

    output_ids = list(
        session.execute(
            select(models.TaskRun.task_output_id).where(
                models.TaskRun.pipeline_run_id.in_(run_ids),
                models.TaskRun.task_output_id.is_not(None),
            )
        )
        .scalars()
        .all()
    )

    session.execute(
        delete(models.TaskRun).where(models.TaskRun.pipeline_run_id.in_(run_ids))
    )

    if output_ids:
        session.execute(
            delete(models.TaskRunOutput).where(models.TaskRunOutput.id.in_(output_ids))
        )

    session.execute(
        delete(models.PipelineRun).where(models.PipelineRun.id.in_(run_ids))
    )


def _delete_data_dirs(run_ids: List[int]) -> int:
    deleted = 0

    for run_id in run_ids:
        try:
            if delete_run_data(run_id):
                deleted += 1
        except (InvalidDataPath, OSError) as error:
            logger.warning(
                "Cannot delete the data of run %s: %s", run_id, error, exc_info=error
            )

    return deleted


def apply_retention(now: Optional[datetime] = None) -> RetentionResult:
    """Apply the configured retention policy. Safe to call at any time."""

    now = now or utcnow()
    result = RetentionResult()

    files_days = settings.retention.files_days
    runs_days = settings.retention.runs_days

    if not files_days and not runs_days:
        return result

    with session_scope() as session:
        if runs_days:
            expired = _finished_runs_before(session, now - timedelta(days=runs_days))

            if expired:
                _delete_runs(session, expired)
                result.deleted_runs = len(expired)
                result.deleted_orphan_files = _delete_data_dirs(expired)

        if files_days:
            # Runs deleted just above are already gone from the database, so
            # this only sees the ones being kept.
            stale = _finished_runs_before(session, now - timedelta(days=files_days))
            result.deleted_run_files = _delete_data_dirs(stale)

    if result:
        logger.info(
            "Retention: deleted %s runs, the log files of %s more, "
            "and %s data directories",
            result.deleted_runs,
            result.deleted_run_files,
            result.deleted_orphan_files,
        )

    return result


def delete_orphan_data() -> int:
    """Delete the data directories of runs that are no longer in the database.

    They are left behind when the database is reset or restored from a backup,
    and nothing else would ever clean them up.
    """

    stored_run_ids = list_stored_run_ids()

    if not stored_run_ids:
        return 0

    with session_scope() as session:
        known = set(
            session.execute(
                select(models.PipelineRun.id).where(
                    models.PipelineRun.id.in_(stored_run_ids)
                )
            )
            .scalars()
            .all()
        )

    orphans = [run_id for run_id in stored_run_ids if run_id not in known]
    deleted = _delete_data_dirs(orphans)

    if deleted:
        logger.info("Retention: deleted %s orphan data directories", deleted)

    return deleted

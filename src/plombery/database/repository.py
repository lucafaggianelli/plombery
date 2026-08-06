"""Database access layer.

Session handling contract
-------------------------

Every function here owns its session and returns objects that are **detached**
from it, fully loaded: whatever the callers read must be loaded before the
session closes, either because it is a plain column or because the query eager
loads the relationship explicitly.

`expire_on_commit` is disabled on the session factory, so an instance keeps the
values it was loaded with after a commit instead of expiring them and trying to
refresh from a session that no longer exists.

When several operations have to happen atomically, don't chain the functions
below: each one commits on its own. Use `session_scope()` and write the queries
inside it, so they share one transaction.
"""

from contextlib import contextmanager
from typing import Collection, Iterator, Optional
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from plombery.schemas import ACTIVE_STATUS, FINISHED_STATUS, PipelineRunStatus
from plombery.utils import utcnow
from .base import SessionLocal
from .schemas import (
    PipelineRunCreate,
    TaskRunCreate,
    TaskRunOutputCreate,
    TaskRunUpdate,
)
from . import models


@contextmanager
def session_scope() -> Iterator[Session]:
    """A transactional scope for a group of operations.

    Commits on success, rolls back on error. Use it when several statements
    have to succeed or fail together.
    """

    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def create_pipeline_run(data: PipelineRunCreate) -> models.PipelineRun:
    with SessionLocal() as db:
        created_model = models.PipelineRun(**data.model_dump())
        db.add(created_model)
        db.commit()
        db.refresh(created_model)

    return created_model


def update_pipeline_run(
    pipeline_run: models.PipelineRun, end_time: datetime, status: PipelineRunStatus
):
    duration = (end_time - pipeline_run.start_time).total_seconds() * 1000

    with SessionLocal() as db:
        db.execute(
            update(models.PipelineRun)
            .where(models.PipelineRun.id == pipeline_run.id)
            .values(end_time=end_time, duration=duration, status=status.value)
        )
        db.commit()

    # The caller holds a detached instance and keeps using it to build the
    # websocket payload and the notifications, so mirror the new values onto it.
    pipeline_run.end_time = end_time
    pipeline_run.duration = duration
    pipeline_run.status = status.value


def list_pipeline_runs(
    pipeline_id: Optional[str] = None,
    trigger_id: Optional[str] = None,
    limit: int = 30,
) -> list[models.PipelineRun]:
    statement = select(models.PipelineRun)

    if pipeline_id:
        statement = statement.where(models.PipelineRun.pipeline_id == pipeline_id)

    if trigger_id:
        statement = statement.where(models.PipelineRun.trigger_id == trigger_id)

    statement = statement.order_by(models.PipelineRun.id.desc()).limit(limit)

    with SessionLocal() as db:
        return list(db.execute(statement).scalars().all())


def get_pipeline_run(pipeline_run_id: int) -> Optional[models.PipelineRun]:
    with SessionLocal() as db:
        return db.execute(
            select(models.PipelineRun)
            # Callers read `task_runs`, which is a relationship, so it has to be
            # loaded before the session closes.
            .options(selectinload(models.PipelineRun.task_runs)).where(
                models.PipelineRun.id == pipeline_run_id
            )
        ).scalar_one_or_none()


def get_latest_pipeline_run(
    pipeline_id: str, trigger_id: str
) -> Optional[models.PipelineRun]:
    with SessionLocal() as db:
        return db.execute(
            select(models.PipelineRun)
            .where(
                models.PipelineRun.pipeline_id == pipeline_id,
                models.PipelineRun.trigger_id == trigger_id,
            )
            .order_by(models.PipelineRun.id.desc())
            .limit(1)
        ).scalar_one_or_none()


def create_task_run(task_run: TaskRunCreate) -> models.TaskRun:
    """Creates a new TaskRun record."""

    with SessionLocal() as session:
        db_task_run = models.TaskRun(
            **task_run.model_dump(exclude_none=True),
            start_time=task_run.start_time or utcnow(),
        )
        session.add(db_task_run)
        session.commit()
        session.refresh(db_task_run)

        return db_task_run


def update_task_run(
    task_run_id: str, update_data: TaskRunUpdate
) -> Optional[models.TaskRun]:
    """Updates an existing TaskRun record and returns it."""

    with SessionLocal() as session:
        session.execute(
            update(models.TaskRun)
            .where(models.TaskRun.id == task_run_id)
            .values(**update_data.model_dump(exclude_none=True))
        )
        session.commit()

        # Re-read in the same session rather than calling get_task_run_by_id,
        # which would open a second one for what is a single operation.
        return session.execute(
            select(models.TaskRun)
            .options(selectinload(models.TaskRun.pipeline_run))
            .where(models.TaskRun.id == task_run_id)
        ).scalar_one_or_none()


def get_task_run_by_id(task_run_id: str) -> Optional[models.TaskRun]:
    """Retrieves a specific TaskRun by ID."""

    with SessionLocal() as db:
        return db.execute(
            select(models.TaskRun)
            # The orchestrator reads `task_run.pipeline_run` to drive the DAG.
            .options(selectinload(models.TaskRun.pipeline_run)).where(
                models.TaskRun.id == task_run_id
            )
        ).scalar_one_or_none()


def get_task_runs_for_pipeline_run(
    run_id: int,
    task_ids: Optional[Collection[str]] = None,
    status: Optional[list[PipelineRunStatus]] = None,
) -> list[models.TaskRun]:
    """
    Retrieves TaskRuns for a specific PipelineRun, optionally filtered by a list of task IDs.
    Used by the Orchestrator for dependency checking and XCom resolution.
    """

    statement = select(models.TaskRun).where(models.TaskRun.pipeline_run_id == run_id)

    if task_ids:
        statement = statement.where(models.TaskRun.task_id.in_(task_ids))

    if status:
        statement = statement.where(models.TaskRun.status.in_(status))

    with SessionLocal() as db:
        return list(db.execute(statement).scalars().all())


def get_active_task_runs(pipeline_run_id: int) -> list[models.TaskRun]:
    """
    Retrieves all TaskRuns for a given PipelineRun that are still active (not COMPLETED/FAILED).
    Used by the Orchestrator to determine pipeline completion.

    Active means:
        * PipelineRunStatus.PENDING
        * PipelineRunStatus.RUNNING
    """
    return get_task_runs_for_pipeline_run(pipeline_run_id, status=ACTIVE_STATUS)


def get_finished_task_runs(pipeline_run_id: int) -> list[models.TaskRun]:
    """
    Retrieves all finished TaskRuns for a given Pipeline.

    Finished means:
        * PipelineRunStatus.COMPLETED
        * PipelineRunStatus.FAILED
        * PipelineRunStatus.CANCELLED
    """
    return get_task_runs_for_pipeline_run(pipeline_run_id, status=FINISHED_STATUS)


def create_task_run_output(
    task_output: TaskRunOutputCreate, task_run_id: str
) -> models.TaskRunOutput:
    """Creates a new TaskRunOutput record and links it to its task run."""

    data = (
        task_output.data.__dict__
        if hasattr(task_output.data, "__dict__")
        else task_output.data
    )

    with SessionLocal() as session:
        db_output = models.TaskRunOutput(
            mimetype=task_output.mimetype,
            encoding=task_output.encoding,
            data=data,
            size=0,
        )
        session.add(db_output)
        # Flush to get the generated ID without ending the transaction: the
        # output row and the link on the task run are written together.
        session.flush()

        session.execute(
            update(models.TaskRun)
            .where(models.TaskRun.id == task_run_id)
            .values(task_output_id=db_output.id)
        )

        session.commit()
        session.refresh(db_output)

        return db_output


def get_task_run_output_by_id(task_output_id: str) -> Optional[models.TaskRunOutput]:
    """Retrieves an TaskRunOutput record by Task Run ID."""

    with SessionLocal() as session:
        return session.get(models.TaskRunOutput, task_output_id)


def mark_tasks_as_skipped(task_ids: set[str], pipeline_run_id: int):
    with session_scope() as session:
        for task_id in task_ids:
            session.add(
                models.TaskRun(
                    task_id=task_id,
                    status=PipelineRunStatus.CANCELLED,
                    pipeline_run_id=pipeline_run_id,
                )
            )

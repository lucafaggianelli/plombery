from typing import Collection, Optional
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import selectinload

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


def create_pipeline_run(data: PipelineRunCreate):
    with SessionLocal() as db:
        db.expire_on_commit = False

        created_model = models.PipelineRun(**data.model_dump())
        db.add(created_model)
        db.commit()
        db.refresh(created_model)
    return created_model


def update_pipeline_run(
    pipeline_run: models.PipelineRun, end_time: datetime, status: PipelineRunStatus
):
    pipeline_run.end_time = end_time
    pipeline_run.duration = (end_time - pipeline_run.start_time).total_seconds() * 1000
    pipeline_run.status = status.value

    with SessionLocal() as db:

        db.query(models.PipelineRun).filter(
            models.PipelineRun.id == pipeline_run.id
        ).update(
            {
                "end_time": end_time,
                "duration": pipeline_run.duration,
                "status": pipeline_run.status,
            }
        )
        db.commit()


def list_pipeline_runs(
    pipeline_id: Optional[str] = None, trigger_id: Optional[str] = None
):
    filters = []
    if pipeline_id:
        filters.append(models.PipelineRun.pipeline_id == pipeline_id)
    if trigger_id:
        filters.append(models.PipelineRun.trigger_id == trigger_id)

    with SessionLocal() as db:
        db.expire_on_commit = False

        pipeline_runs: list[models.PipelineRun] = (
            db.query(models.PipelineRun)
            .filter(*filters)
            .order_by(models.PipelineRun.id.desc())
            .limit(30)
            .all()
        )

    return pipeline_runs


def get_pipeline_run(pipeline_run_id: int) -> Optional[models.PipelineRun]:
    with SessionLocal() as db:

        pipeline_run: Optional[models.PipelineRun] = (
            db.query(models.PipelineRun)
            .options(selectinload(models.PipelineRun.task_runs))
            .get(pipeline_run_id)
        )

    return pipeline_run


def get_latest_pipeline_run(pipeline_id, trigger_id):
    with SessionLocal() as db:

        pipeline_run: models.PipelineRun = (
            db.query(models.PipelineRun)
            .filter(
                models.PipelineRun.pipeline_id == pipeline_id,
                models.PipelineRun.trigger_id == trigger_id,
            )
            .order_by(models.PipelineRun.id.desc())
            .first()
        )

    return pipeline_run


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
    """Updates an existing TaskRun record."""
    with SessionLocal() as session:
        session.execute(
            update(models.TaskRun)
            .where(models.TaskRun.id == task_run_id)
            .values(**update_data.model_dump(exclude_none=True))
        )

        session.commit()
        return get_task_run_by_id(task_run_id)


def get_task_run_by_id(task_run_id: str) -> Optional[models.TaskRun]:
    """Retrieves a specific TaskRun by ID."""
    with SessionLocal() as db:
        return (
            db.query(models.TaskRun)
            .options(selectinload(models.TaskRun.pipeline_run))
            .get(task_run_id)
        )


def get_task_runs_for_pipeline_run(
    run_id: int,
    task_ids: Optional[Collection[str]] = None,
    status: Optional[list[PipelineRunStatus]] = None,
) -> list[models.TaskRun]:
    """
    Retrieves TaskRuns for a specific PipelineRun, optionally filtered by a list of task IDs.
    Used by the Orchestrator for dependency checking and XCom resolution.
    """
    with SessionLocal() as db:
        stmt = db.query(models.TaskRun).where(models.TaskRun.pipeline_run_id == run_id)

        if task_ids:
            stmt = stmt.where(models.TaskRun.task_id.in_(task_ids))

        if status:
            stmt = stmt.where(models.TaskRun.status.in_(status))

        return stmt.all()


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
    """Creates a new TaskRunOutput record and returns the instance."""
    with SessionLocal() as session:
        data = (
            task_output.data.__dict__
            if hasattr(task_output.data, "__dict__")
            else task_output.data
        )

        db_output = models.TaskRunOutput(
            mimetype=task_output.mimetype,
            encoding=task_output.encoding,
            data=data,
            size=0,
        )
        session.add(db_output)
        session.flush()

        session.query(models.TaskRun).filter(models.TaskRun.id == task_run_id).update(
            {
                "task_output_id": db_output.id,
            },
            # Crucial for bulk updates in a transaction
            synchronize_session=False,
        )

        session.commit()
        session.refresh(db_output)
        return db_output


def get_task_run_output_by_id(task_output_id: str) -> Optional[models.TaskRunOutput]:
    """Retrieves an TaskRunOutput record by Task Run ID."""
    with SessionLocal() as session:
        return session.query(models.TaskRunOutput).get(task_output_id)


def mark_tasks_as_skipped(task_ids: set[str], pipeline_run_id: int):
    with SessionLocal() as session:
        for task_id in task_ids:
            session.add(
                models.TaskRun(
                    task_id=task_id,
                    status=PipelineRunStatus.CANCELLED,
                    pipeline_run_id=pipeline_run_id,
                )
            )

        session.commit()

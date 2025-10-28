import os
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, and_, or_

from plombery.constants import MANUAL_TRIGGER_ID
from plombery.database.base import Base, SessionLocal, engine
from plombery.database.models import PipelineRun
from plombery.schemas import PipelineRunStatus


INITIAL_REVISION_ID = "cd90ef97cbc9"


def _run_migrations():
    """
    Run Alembic migrations considering that Alembic was introduced later, so some users
    might already have a DB that wasn't initialized by Alembic.
    The strategy is
    """

    alembic_ini = (Path(__file__).parent.parent / "alembic" / "alembic.ini").absolute()

    alembic_cfg = Config(alembic_ini)

    db_already_exists = _check_for_existing_db()

    if db_already_exists:
        print("Existing table found. Assuming pre-Alembic setup.")

        # Stamp the DB with the initial revision ID
        # This tells Alembic that the work of the first migration is already done.
        # This action *does not run* any migration SQL, only updates the alembic_version table.
        # We stamp to the *initial* revision so that the *next* upgrade starts from there.
        print(f"Stamping database with revision: {INITIAL_REVISION_ID}")
        command.stamp(alembic_cfg, INITIAL_REVISION_ID)
    else:
        # Empty DB (or table not found) - run all migrations from base to head
        print("Running all migrations from base to head...")

    command.upgrade(alembic_cfg, "head")

    print("Alembic migrations complete.")


def _check_for_existing_db() -> bool:
    """
    Checks if the database is present and if a critical table already exists.
    """
    try:
        with SessionLocal() as db:
            inspector = inspect(db.get_bind())

            # Check for the existence of initial schema table
            return inspector.has_table("pipeline_runs") and not inspector.has_table(
                "alembic_version"
            )
    except Exception:
        # This will catch errors like 'database does not exist' for some dialects
        # or connection errors. For SQLite, an empty file is often created,
        # so relying on has_table is more robust.
        return False


def _mark_cancelled_runs():
    """
    Mark stuck runs as cancelled at the service startup, this is needed when the service restarts
    while some runs are still running.
    In the future this should be handled better, think if there are multiple nodes, this would
    mark running jobs as cancelled while they're run by another node.
    """

    stuck_runs_filter = or_(
        PipelineRun.status == PipelineRunStatus.RUNNING,
        and_(
            PipelineRun.status == PipelineRunStatus.PENDING,
            PipelineRun.trigger_id == MANUAL_TRIGGER_ID,
        ),
    )

    with SessionLocal() as db:
        db.query(PipelineRun).filter(stuck_runs_filter).update(
            dict(
                status=PipelineRunStatus.CANCELLED,
            )
        )

        db.commit()


def setup_database():
    if os.getenv("TESTING", "false") == "true":
        # During testing, Alembic migrations are not correctly applied
        # so just skip them and create the DB from scratch
        Base.metadata.create_all(bind=engine)
    else:
        _run_migrations()
    _mark_cancelled_runs()

from typing import List

from fastapi.encoders import jsonable_encoder
from pydantic import parse_obj_as
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from plombery.database.base import Base, engine, SessionLocal
from plombery.schemas import PipelineRunStatus, TaskRun


class PydanticType(sa.types.TypeDecorator):
    """
    Source: https://gist.github.com/imankulov/4051b7805ad737ace7d8de3d3f934d6b

    Pydantic type.
    SAVING:
    - Uses SQLAlchemy JSON type under the hood.
    - Acceps the pydantic model and converts it to a dict on save.
    - SQLAlchemy engine JSON-encodes the dict to a string.
    RETRIEVING:
    - Pulls the string from the database.
    - SQLAlchemy engine JSON-decodes the string to a dict.
    - Uses the dict to create a pydantic model.
    """

    # If you work with PostgreSQL, you can consider using
    # sqlalchemy.dialects.postgresql.JSONB instead of a
    # generic sa.types.JSON
    #
    # Ref: https://www.postgresql.org/docs/13/datatype-json.html
    impl = sa.types.JSON

    def __init__(self, pydantic_type):
        super().__init__()
        self.pydantic_type = pydantic_type

    def load_dialect_impl(self, dialect):
        # Use JSONB for PostgreSQL and JSON for other databases.
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(sa.JSON())

    def process_bind_param(self, value, dialect):
        return jsonable_encoder(value) if value else None

    def process_result_value(self, value, dialect):
        return parse_obj_as(self.pydantic_type, value) if value else None


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(String, index=True)
    trigger_id = Column(String)
    status = Column(String)
    start_time = Column(DateTime)
    duration = Column(Integer, default=0)
    tasks_run = Column(PydanticType(List[TaskRun]))


Base.metadata.create_all(bind=engine)


def _mark_cancelled_runs():
    db = SessionLocal()

    db.query(PipelineRun).filter(PipelineRun.status == PipelineRunStatus.RUNNING.value).update(
        dict(
            status=PipelineRunStatus.CANCELLED.value,
        )
    )

    db.commit()


_mark_cancelled_runs()

from typing import Any, Optional
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Integer, String, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from uuid6 import uuid7

from plombery.database.base import Base
from plombery.database.type_helpers import AwareDateTime, PydanticType


def uuid_pkey():
    return mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid7()),
    )


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    # should be uuid, though it can't be converted due to SQLite
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # should be non-nullable, though it can't be converted due to SQLite
    pipeline_id: Mapped[str] = mapped_column(String, index=True, nullable=True)
    # should be non-nullable, though it can't be converted due to SQLite
    trigger_id: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(AwareDateTime, nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(AwareDateTime, nullable=True)
    duration: Mapped[int] = mapped_column(default=0, nullable=True)
    input_params: Mapped[Optional[dict]] = mapped_column(
        PydanticType(Optional[dict]), default=None, nullable=True
    )
    reason: Mapped[Optional[str]]

    task_runs: Mapped[list["TaskRun"]] = relationship(back_populates="pipeline_run")

    __table_args__ = (Index("idx_pipeline_status", "pipeline_id", "status"),)


class TaskRun(Base):
    """
    Model to store the execution and output details for a single task instance.
    """

    __tablename__ = "task_runs"

    id: Mapped[str] = uuid_pkey()
    pipeline_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipeline_runs.id"), nullable=False
    )
    task_id: Mapped[str]

    status: Mapped[str]
    start_time: Mapped[datetime] = mapped_column(AwareDateTime, nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(AwareDateTime, nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Context (Data necessary for DAG flow and execution)
    # Resolved arguments/inputs for the task instance
    context: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationship back to the PipelineRun
    pipeline_run: Mapped[PipelineRun] = relationship(back_populates="task_runs")

    # Task output
    task_output_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("task_run_outputs.id"), nullable=True
    )
    task_output: Mapped["TaskRunOutput"] = relationship(
        back_populates="task_run", uselist=False
    )

    # Mapping or Fan-in/out

    # Index for dynamic mapping (NULL if not a mapped task)
    map_index: Mapped[Optional[int]] = mapped_column(nullable=True, index=True)

    # The ID of the specific TaskRun instance that generated the input list/item.
    parent_task_run_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("task_runs.id"), nullable=True
    )
    parent_task_run: Mapped[Optional["TaskRun"]] = relationship(
        back_populates="mapped_task_runs", remote_side=[id]
    )
    mapped_task_runs: Mapped[list["TaskRun"]] = relationship(
        back_populates="parent_task_run"
    )

    __table_args__ = (
        Index(
            "idx_taskrun_pipeline",
            "pipeline_run_id",
            "task_id",
            "map_index",
            unique=True,
        ),
        Index("idx_taskrun_status", "status"),
    )


class TaskRunOutput(Base):
    """Stores the Cross-Communication data, i.e., the task run output."""

    __tablename__ = "task_run_outputs"

    id: Mapped[str] = uuid_pkey()

    mimetype: Mapped[str]
    size: Mapped[int]
    encoding: Mapped[Optional[str]]

    # Store the actual output data. Use JSON for serializable objects,
    # or a dedicated column type for large binary data/URIs (e.g., S3 pointer)
    data: Mapped[Any] = mapped_column(JSON, nullable=False)

    task_run: Mapped[TaskRun] = relationship(back_populates="task_output")

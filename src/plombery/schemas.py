from datetime import datetime
from typing import Any, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, NonNegativeFloat


class PipelineRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def is_finished(self) -> bool:
        return self in [
            PipelineRunStatus.COMPLETED,
            PipelineRunStatus.FAILED,
            PipelineRunStatus.CANCELLED,
        ]


ACTIVE_STATUS = [PipelineRunStatus.PENDING, PipelineRunStatus.RUNNING]
FINISHED_STATUS = [
    PipelineRunStatus.COMPLETED,
    PipelineRunStatus.FAILED,
    PipelineRunStatus.CANCELLED,
]


class TaskOutputData(BaseModel):
    """
    The output of a task.
    """

    id: str
    data: Any
    mimetype: Optional[str]
    size: int


class TaskRun(BaseModel):
    id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[NonNegativeFloat] = 0
    """Task duration in milliseconds"""
    context: Optional[dict]
    """True if the task generated an output"""
    status: Optional[PipelineRunStatus] = PipelineRunStatus.PENDING
    task_id: str
    task_output_id: Optional[str]
    map_index: Optional[int] = None
    parent_task_run_id: Optional[str] = None

    class Config:
        from_attributes = True


class NotificationRule(BaseModel):
    channels: List[str]
    pipeline_status: List[PipelineRunStatus] = Field(
        default_factory=lambda: [PipelineRunStatus.FAILED]
    )

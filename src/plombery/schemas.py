from datetime import datetime
from typing import Any, List, Literal, Optional
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat


class PipelineIssue(BaseModel):
    """A problem found while checking a pipeline at startup.

    An `error` means the pipeline can't run as it is (a required secret that
    isn't set); a `warning` is worth surfacing but doesn't stop it. `task_id`
    scopes the issue to a single task when it belongs to one.
    """

    level: Literal["error", "warning"] = "error"
    code: str
    message: str
    task_id: Optional[str] = None


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
    mimetype: Optional[str] = None
    encoding: Optional[str] = None
    size: int

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class NotificationRule(BaseModel):
    channels: List[str]
    pipeline_status: List[PipelineRunStatus] = Field(
        default_factory=lambda: [PipelineRunStatus.FAILED]
    )

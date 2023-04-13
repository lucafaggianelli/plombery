from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, PositiveInt


class PipelineRunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskRun(BaseModel):
    duration: Optional[PositiveInt]
    """Task duration in milliseconds"""
    has_output: bool = False
    """True if the task generated an output"""
    status: Optional[PipelineRunStatus]
    task_id: str

    class Config:
        orm_mode = True


class NotificationRule(BaseModel):
    channels: List[str]
    pipeline_status: List[PipelineRunStatus] = Field(
        default_factory=lambda: [PipelineRunStatus.FAILED]
    )

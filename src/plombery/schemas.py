from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, NonNegativeFloat


class PipelineRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskRun(BaseModel):
    duration: Optional[NonNegativeFloat] = 0
    """Task duration in milliseconds"""
    has_output: bool = False
    """True if the task generated an output"""
    status: Optional[PipelineRunStatus] = PipelineRunStatus.PENDING
    task_id: str

    class Config:
        from_attributes = True


class NotificationRule(BaseModel):
    channels: List[str]
    pipeline_status: List[PipelineRunStatus] = Field(
        default_factory=lambda: [PipelineRunStatus.FAILED]
    )

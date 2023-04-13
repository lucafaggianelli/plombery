from typing import List
from enum import Enum

from pydantic import BaseModel, Field


class PipelineRunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationRule(BaseModel):
    channels: List[str]
    pipeline_status: List[PipelineRunStatus] = Field(
        default_factory=lambda: [PipelineRunStatus.FAILED]
    )

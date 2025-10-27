from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from plombery.schemas import PipelineRunStatus, TaskRun


class PipelineRunBase(BaseModel):
    pipeline_id: str
    trigger_id: str
    status: PipelineRunStatus
    start_time: datetime
    tasks_run: List[TaskRun] = Field(default_factory=list)
    input_params: Optional[None] = None
    reason: Optional[str] = None

    class Config:
        from_attributes = True


class PipelineRun(PipelineRunBase):
    id: int
    duration: float


class PipelineRunCreate(PipelineRunBase):
    pass

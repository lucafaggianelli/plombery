from typing import List
from datetime import datetime

from pydantic import BaseModel, Field

from plombery.schemas import PipelineRunStatus, TaskRun


class PipelineRunBase(BaseModel):
    pipeline_id: str
    trigger_id: str
    status: PipelineRunStatus
    start_time: datetime
    tasks_run: List[TaskRun] = Field(default_factory=list)

    class Config:
        from_attributes = True


class PipelineRun(PipelineRunBase):
    id: int
    duration: float


class PipelineRunCreate(PipelineRunBase):
    pass

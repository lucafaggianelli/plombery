from typing import List
from datetime import datetime

from pydantic import BaseModel

from plombery.schemas import PipelineRunStatus, TaskRun


class PipelineRunBase(BaseModel):
    pipeline_id: str
    trigger_id: str
    status: PipelineRunStatus
    start_time: datetime

    class Config:
        orm_mode = True


class PipelineRun(PipelineRunBase):
    id: int
    duration: int
    tasks_run: List[TaskRun]


class PipelineRunCreate(PipelineRunBase):
    pass

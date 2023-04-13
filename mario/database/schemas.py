from typing import Dict
from datetime import datetime

from pydantic import BaseModel

from mario.schemas import PipelineRunStatus, TaskRun


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
    tasks_run: Dict[str, TaskRun]


class PipelineRunCreate(PipelineRunBase):
    pass

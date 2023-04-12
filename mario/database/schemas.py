from datetime import datetime

from pydantic import BaseModel

from mario.schemas import PipelineRunStatus


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


class PipelineRunCreate(PipelineRunBase):
    pass

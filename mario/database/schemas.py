from datetime import datetime

from pydantic import BaseModel


class PipelineRunBase(BaseModel):
    pipeline_id: str
    trigger_id: str
    status: str
    start_time: datetime

    class Config:
        orm_mode = True


class PipelineRun(PipelineRunBase):
    id: int
    duration: int


class PipelineRunCreate(PipelineRunBase):
    pass

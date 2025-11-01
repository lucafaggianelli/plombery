from typing import Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from plombery.schemas import PipelineRunStatus, TaskRun


class PipelineRunBase(BaseModel):
    pipeline_id: str
    trigger_id: str
    status: PipelineRunStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    input_params: Optional[dict] = None
    reason: Optional[str] = None

    class Config:
        from_attributes = True


class PipelineRun(PipelineRunBase):
    id: int
    duration: float


class PipelineRunWithTaskRuns(PipelineRun):
    task_runs: list[TaskRun] = Field(default_factory=list)


class PipelineRunCreate(PipelineRunBase):
    pass


class TaskRunCreate(BaseModel):
    """Schema for creating a new TaskRun record."""

    pipeline_run_id: int
    task_id: str
    status: PipelineRunStatus
    start_time: Optional[datetime] = None
    context: Optional[dict[str, Any]] = None
    parent_task_run_id: Optional[str] = None
    map_index: Optional[int] = None


class TaskRunUpdate(BaseModel):
    """Schema for updating an existing TaskRun record after execution."""

    status: PipelineRunStatus
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    task_output_id: Optional[str] = None


class TaskRunOutputCreate(BaseModel):
    """Schema for creating a new Task Run Output record."""

    data: Any
    mimetype: Optional[str] = "application/json"
    encoding: Optional[str] = "utf-8"

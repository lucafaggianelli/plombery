from typing import List

from sqlalchemy import Column, Integer, String

from plombery.database.base import Base
from plombery.database.type_helpers import AwareDateTime, PydanticType
from plombery.schemas import TaskRun


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(String, index=True)
    trigger_id = Column(String)
    status = Column(String)
    start_time = Column(AwareDateTime)
    duration = Column(Integer, default=0)
    tasks_run = Column(PydanticType(List[TaskRun]), default=list)
    input_params = Column(PydanticType(dict), default=None)
    reason = Column(String, default=None)

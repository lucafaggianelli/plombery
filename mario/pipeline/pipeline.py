from typing import List
from enum import Enum
import logging

from pydantic import BaseModel

from .task import Task
from .trigger import Trigger
from ._utils import to_snake_case, prettify_name


class PipelineRunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Pipeline:
    id: str
    name: str = None
    description: str = None
    params: BaseModel = None
    tasks: List[Task] = []
    triggers: List[Trigger] = []

    def __init__(self) -> None:
        self.id = to_snake_case(self.__class__.__name__)
        self.name = prettify_name(self.id).title()
        self.description = self.__class__.__doc__

        self.logger = logging.getLogger(f"[P]{self.id}")

from typing import List
import logging

from pydantic import BaseModel

from .task import Task
from .trigger import Trigger
from ._utils import to_snake_case


class Pipeline:
    params: BaseModel = None
    tasks: List[Task] = []
    triggers: List[Trigger] = []

    def __init__(self) -> None:
        self.uuid = to_snake_case(self.__class__.__name__)
        self.logger = logging.getLogger(f"[P]{self.uuid}")

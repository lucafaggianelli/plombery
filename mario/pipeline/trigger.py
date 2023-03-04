from typing import Union, Callable

from apscheduler.triggers.base import BaseTrigger
from pydantic import BaseModel


class Trigger(BaseModel):
    name: str
    aps_trigger: BaseTrigger
    params: Union[dict, list, Callable] = None
    paused: bool = False

    class Config:
        arbitrary_types_allowed = True

from apscheduler.triggers.base import BaseTrigger
from pydantic import BaseModel


class Trigger(BaseModel):
    id: str
    name: str
    aps_trigger: BaseTrigger
    description: str = __doc__
    params: dict = None
    paused: bool = False

    class Config:
        arbitrary_types_allowed = True

from datetime import datetime

from apscheduler.triggers.base import BaseTrigger
from pydantic import BaseModel


class Trigger(BaseModel):
    id: str
    name: str
    schedule: BaseTrigger
    description: str = __doc__
    params: dict = None
    paused: bool = False
    next_fire_time: datetime = None

    class Config:
        arbitrary_types_allowed = True

        json_encoders = {
            BaseTrigger: lambda v: str(v),
        }

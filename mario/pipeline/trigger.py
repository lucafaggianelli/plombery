from apscheduler.triggers.base import BaseTrigger
from pydantic import BaseModel, Field


class Trigger(BaseModel):
    id: str
    name: str
    aps_trigger: BaseTrigger = Field(exclude=True)
    description: str = __doc__
    params: dict = None
    paused: bool = False

    class Config:
        arbitrary_types_allowed = True

        json_encoders = {
            BaseTrigger: lambda v: str(v),
        }

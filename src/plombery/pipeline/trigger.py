from datetime import datetime
from typing import Annotated, Optional

from apscheduler.triggers.base import BaseTrigger
from pydantic import BaseModel, ConfigDict, PlainSerializer


class Trigger(BaseModel):
    id: str
    name: str
    schedule: Annotated[BaseTrigger, PlainSerializer(str)]
    description: Optional[str] = __doc__
    params: Optional[BaseModel] = None
    paused: bool = False
    next_fire_time: Optional[datetime] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

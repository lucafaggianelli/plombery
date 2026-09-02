from datetime import datetime
from typing import Annotated

from apscheduler.triggers.base import BaseTrigger
from pydantic import (
    BaseModel,
    ConfigDict,
    PlainSerializer,
    SerializeAsAny,
    WithJsonSchema,
)


class Trigger(BaseModel):
    id: str
    name: str
    schedule: Annotated[BaseTrigger, PlainSerializer(str)]
    description: str | None = __doc__
    # `SerializeAsAny` so the params keep the fields of whichever model the
    # pipeline declared: annotated as a plain `BaseModel`, pydantic would
    # serialize them with the base class' (empty) serializer and the API would
    # answer `{}` for every trigger. The schema is stated by hand for the same
    # reason — the concrete model isn't known here, so what a client gets is an
    # arbitrary JSON object.
    params: Annotated[
        SerializeAsAny[BaseModel | None],
        WithJsonSchema({"anyOf": [{"type": "object"}, {"type": "null"}]}),
    ] = None
    paused: bool = False
    next_fire_time: datetime | None = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

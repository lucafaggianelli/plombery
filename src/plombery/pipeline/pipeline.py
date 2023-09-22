from typing import Any, List, Optional, Type

from pydantic import BaseModel, Field, model_validator

from .task import Task
from .trigger import Trigger
from ._utils import prettify_name


class Pipeline(BaseModel):
    id: str
    tasks: List[Task]
    name: Optional[str]
    description: Optional[str] = None
    params: Optional[Type[BaseModel]] = Field(exclude=True, default=None)
    triggers: List[Trigger] = Field(default_factory=list)

    class Config:
        validate_assignment = True

    @model_validator(mode="before")
    @classmethod
    def generate_default_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("name", None):
                data["name"] = prettify_name(data["id"]).title()

            if not data.get("description", None):
                data["description"] = cls.__doc__

        return data

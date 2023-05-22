from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field, validator

from .task import Task
from .trigger import Trigger
from ._utils import prettify_name


class Pipeline(BaseModel):
    id: str
    tasks: List[Task]
    name: Optional[str] = None
    description: Optional[str] = None
    params: Optional[Type[BaseModel]] = Field(exclude=True, default=None)
    triggers: Optional[List[Trigger]] = Field(default_factory=list)

    class Config:
        validate_assignment = True

    @validator("name", always=True)
    def generate_default_name(cls, name: str, values: Dict[str, Any]) -> str:
        if not name:
            return prettify_name(values["id"]).title()

        return name

    @validator("description", always=True)
    def generate_default_description(
        cls, description: str, values: Dict[str, Any]
    ) -> str:
        if not description:
            return cls.__doc__

        return description

    @validator("triggers", pre=True, always=True)
    def set_name(cls, triggers):
        return triggers or []

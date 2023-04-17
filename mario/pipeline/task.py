from typing import Any, Callable, Dict

from pydantic import BaseModel, validator, Field

from ._utils import prettify_name


class Task(BaseModel):
    id: str
    run: Callable = Field(exclude=True)
    name: str = None
    description: str = None

    @validator("name", always=True)
    def generate_default_name(cls, name: str, values: Dict[str, Any]) -> str:
        if not name:
            return prettify_name(values["id"]).title()

        return name

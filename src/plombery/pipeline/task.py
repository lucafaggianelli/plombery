from typing import Any, Callable, Optional

from pydantic import BaseModel, model_validator, Field

from ._utils import prettify_name


class Task(BaseModel):
    id: str
    run: Callable = Field(
        exclude=True,
    )
    name: Optional[str]
    description: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def generate_default_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("name", None):
                data["name"] = prettify_name(data["id"]).title()

        return data

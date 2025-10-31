import datetime

from fastapi.encoders import jsonable_encoder
from pydantic import TypeAdapter
import sqlalchemy as sa
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB


class PydanticType(sa.types.TypeDecorator):
    """
    Source: https://gist.github.com/imankulov/4051b7805ad737ace7d8de3d3f934d6b

    Pydantic type.
    SAVING:
    - Uses SQLAlchemy JSON type under the hood.
    - Acceps the pydantic model and converts it to a dict on save.
    - SQLAlchemy engine JSON-encodes the dict to a string.
    RETRIEVING:
    - Pulls the string from the database.
    - SQLAlchemy engine JSON-decodes the string to a dict.
    - Uses the dict to create a pydantic model.
    """

    # If you work with PostgreSQL, you can consider using
    # sqlalchemy.dialects.postgresql.JSONB instead of a
    # generic sa.types.JSON
    #
    # Ref: https://www.postgresql.org/docs/13/datatype-json.html
    impl = sa.types.JSON

    cache_ok = True

    def __init__(self, pydantic_type):
        super().__init__()
        self.adapter = TypeAdapter(pydantic_type)

    def load_dialect_impl(self, dialect):
        # Use JSONB for PostgreSQL and JSON for other databases.
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(sa.JSON())

    def process_bind_param(self, value, dialect):
        return jsonable_encoder(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return self.adapter.validate_python(value) if value is not None else None


class AwareDateTime(sa.types.TypeDecorator):
    """
    Results returned as timezone-aware datetimes (UTC timezone),
    not naive ones.
    """

    impl = DateTime

    def process_result_value(self, value: datetime.datetime, dialect):
        return value.replace(tzinfo=datetime.timezone.utc) if value else value

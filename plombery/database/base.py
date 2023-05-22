import json

from pydantic.json import pydantic_encoder
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from plombery.config import settings


def json_serializer(*args, **kwargs) -> str:
    return json.dumps(*args, default=pydantic_encoder, **kwargs)


engine = create_engine(
    settings.database_url,
    json_serializer=json_serializer,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

import json

from fastapi.encoders import jsonable_encoder
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from plombery.config import settings


def json_serializer(*args, **kwargs) -> str:
    return json.dumps(*args, default=jsonable_encoder, **kwargs)


def get_engine(poolclass=None):
    return create_engine(
        settings.database_url,
        json_serializer=json_serializer,
        connect_args=connect_args,
        poolclass=poolclass,
    )


connect_args = {}

if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

if settings.database_url.startswith("sqlite+libsql"):
    try:
        import sqlalchemy_libsql  # noqa: F401
    except ImportError:
        raise Exception(
            "To use libsql install the package sqlalchemy-libsql",
        )

    connect_args["auth_token"] = settings.database_auth_token


engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

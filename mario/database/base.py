from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from mario.config import settings


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

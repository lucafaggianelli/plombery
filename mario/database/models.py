from sqlalchemy import Column, Integer, String, DateTime

from mario.database.base import Base, engine, SessionLocal
from mario.pipeline.pipeline import PipelineRunStatus


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(String, index=True)
    trigger_id = Column(String)
    status = Column(String)
    start_time = Column(DateTime)
    duration = Column(Integer, default=0)


Base.metadata.create_all(bind=engine)


def _mark_cancelled_runs():
    db = SessionLocal()

    db.query(PipelineRun).filter(PipelineRun.status == PipelineRunStatus.RUNNING.value).update(
        dict(
            status=PipelineRunStatus.CANCELLED.value,
        )
    )

    db.commit()


_mark_cancelled_runs()

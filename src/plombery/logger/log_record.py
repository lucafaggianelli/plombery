import logging
from typing import Optional


class ExtendedLogRecord(logging.LogRecord):
    pipeline: str
    run_id: int
    task: Optional[str]

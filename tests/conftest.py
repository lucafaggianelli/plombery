from collections import Counter
from typing import Dict, Generator
import asyncio
import os
from pathlib import Path

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from plombery import _Plombery
from plombery.config import settings
from plombery.database.base import Base, engine
from plombery.database.models import PipelineRun
from plombery.database.repository import get_pipeline_run
from plombery.orchestrator import data_storage, orchestrator
from plombery.config.model import AuthSettings
from plombery.api import app as fastapi_app
from plombery.api.authentication import _needs_auth
from plombery.schemas import FINISHED_STATUS


def _bypass_auth():
    return {
        "name": "Test User",
        "email": "test@email.com",
    }


async def wait_for_run(run_id: int, timeout: float = 10.0) -> PipelineRun:
    """Wait for a pipeline run to reach a final status.

    Pipelines are executed asynchronously, task by task, so a test has to wait
    for the DAG to drain before asserting on the result. Returns the run as it
    is when the timeout expires, so that a test can assert on a run that never
    finished.
    """

    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout

    while loop.time() < deadline:
        run = get_pipeline_run(run_id)

        if run and run.status in FINISHED_STATUS:
            # Give any concurrent task a chance to (wrongly) schedule more work,
            # so that tests asserting "runs exactly once" are meaningful.
            await asyncio.sleep(0.1)
            return get_pipeline_run(run_id)

        await asyncio.sleep(0.05)

    return get_pipeline_run(run_id)


def count_task_runs(run: PipelineRun) -> Dict[str, int]:
    """Number of task runs per task ID, to assert on fan-out and duplicates."""

    return dict(Counter(task_run.task_id for task_run in run.task_runs))


@pytest.fixture
def app():
    # The engine is created once at import time and the in memory database
    # lives as long as the process, so without this every test would see the
    # rows left behind by the ones that ran before it.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # The orchestrator is a module level singleton and its scheduler binds to
    # the event loop that started it, while every test gets a fresh event loop.
    # Reset both the registry and the scheduler so that more than one test can
    # actually run a pipeline.
    orchestrator._all_pipelines.clear()
    orchestrator._all_triggers.clear()
    orchestrator.scheduler = AsyncIOScheduler()

    plombery_app = _Plombery()

    yield plombery_app

    try:
        if orchestrator.scheduler.running:
            orchestrator.scheduler.shutdown(wait=False)
    except RuntimeError:
        # The event loop fixture may have closed the loop already, in which case
        # the scheduler is gone with it and there is nothing left to shut down.
        pass


@pytest.fixture
def with_auth():
    # Enable auth
    settings.auth = AuthSettings(
        client_id="test-client-id",
        client_secret="test-client-secret",
        access_token_url="https://authservice.com/token",
        authorize_url="https://authservice.com/authorize",
        jwks_uri="https://authservice.com/keys",
    )

    yield None


@pytest.fixture
def authenticated():
    fastapi_app.dependency_overrides[_needs_auth] = _bypass_auth


@pytest.fixture(autouse=True)
def set_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    print(f"CWD = {tmp_path}")
    os.chdir(tmp_path)

    # `_base_data_path` is resolved once, at import time, so changing the working
    # directory is not enough to keep runs data and log files isolated between
    # tests: they would all keep appending to the very first temp directory.
    monkeypatch.setattr(
        data_storage, "_base_data_path", (tmp_path / ".data").absolute()
    )

    yield tmp_path


@pytest.fixture(autouse=True)
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

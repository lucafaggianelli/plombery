from typing import Generator
import asyncio
import os
from pathlib import Path

import pytest

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from plombery import _Plombery
from plombery.config import settings
from plombery.config.model import AuthSettings
from plombery.api import app as fastapi_app
from plombery.api.authentication import _needs_auth
from plombery.orchestrator import orchestrator


def _bypass_auth():
    return {
        "name": "Test User",
        "email": "test@email.com",
    }


@pytest.fixture
def app():
    plombery_app = _Plombery()
    yield plombery_app


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
def set_cwd(tmp_path: Path):
    print(f"CWD = {tmp_path}")
    os.chdir(tmp_path)
    yield tmp_path


@pytest.fixture(autouse=True)
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_orchestrator():
    """Reset the module-global orchestrator's state between tests.

    The orchestrator's scheduler binds to the event loop running when
    `start()` is first called; subsequent tests get a fresh event loop
    (see the `event_loop` fixture) but APScheduler still holds the closed
    one, raising `RuntimeError: Event loop is closed`. Likewise the
    orchestrator's class-level pipeline/trigger registries persist across
    tests. Resetting both ensures each test starts clean.

    We replace the scheduler with a fresh instance rather than calling
    shutdown() on the old one — shutdown itself schedules work on the
    (already-closed) event loop and raises.
    """
    yield
    orchestrator.scheduler = AsyncIOScheduler()
    orchestrator._all_pipelines.clear()
    orchestrator._all_triggers.clear()

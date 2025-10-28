from typing import Generator
import asyncio
import os
from pathlib import Path

import pytest

from plombery import _Plombery
from plombery.config import settings
from plombery.config.model import AuthSettings
from plombery.api import app as fastapi_app
from plombery.api.authentication import _needs_auth


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

from typing import Generator
import asyncio
import os
from pathlib import Path

import pytest

from mario import Mario
from mario.config import settings, AuthSettings
from mario.api import api as fastapi_app
from mario.api.authentication import _needs_auth


def _bypass_auth():
    return {
        "name": "Test User",
        "email": "test@email.com",
    }


@pytest.fixture
def app():
    mario_app = Mario()
    yield mario_app


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

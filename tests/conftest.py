import os
from pathlib import Path
from typing import Generator
import asyncio

import pytest


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

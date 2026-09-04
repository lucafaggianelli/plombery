"""Tests for the blocked event loop watchdog."""

import asyncio
import logging
import time

import pytest

from plombery import Pipeline, task, _Plombery as Plombery
from plombery.orchestrator import run_pipeline_now
from plombery.orchestrator.watchdog import start_watchdog, stop_watchdog

from .conftest import wait_for_run


@pytest.fixture
def watchdog_warnings(caplog):
    """`start_watchdog` needs a running loop, so the test starts it itself."""

    caplog.set_level(logging.WARNING, logger="plombery")
    yield caplog
    stop_watchdog()


def blocked_loop_warnings(caplog) -> list:
    return [
        record.getMessage()
        for record in caplog.records
        if "event loop was blocked" in record.getMessage()
    ]


@pytest.mark.asyncio
async def test_a_blocking_async_task_is_reported(app: Plombery, watchdog_warnings):
    """An async task calling blocking code holds the loop, and the whole app
    with it: the watchdog turns that into a warning naming the task."""

    app.start()
    # app.start() already started one with the configured threshold
    stop_watchdog()
    start_watchdog(threshold_seconds=0.3)

    with Pipeline(id="blocking-async") as pipeline:

        @task
        async def blocks_the_loop():
            time.sleep(1)

    app.register_pipeline(pipeline)

    await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=6)

    # Let the watchdog probe once more after the loop is free again
    await asyncio.sleep(0.5)

    warnings = blocked_loop_warnings(watchdog_warnings)

    assert warnings, "the blocked loop went unreported"
    assert "blocks_the_loop" in warnings[0]


@pytest.mark.asyncio
async def test_a_sync_task_is_not_reported(app: Plombery, watchdog_warnings):
    """A plain `def` task runs in a thread, so it never holds the loop."""

    app.start()
    # app.start() already started one with the configured threshold
    stop_watchdog()
    start_watchdog(threshold_seconds=0.3)

    with Pipeline(id="blocking-sync") as pipeline:

        @task
        def runs_in_a_thread():
            time.sleep(1)

    app.register_pipeline(pipeline)

    await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=6)
    await asyncio.sleep(0.5)

    warnings = blocked_loop_warnings(watchdog_warnings)

    assert not warnings, f"a threaded task should not block the loop: {warnings}"

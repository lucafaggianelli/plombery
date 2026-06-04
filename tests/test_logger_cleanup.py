"""Regression test for issue #491 — file-descriptor leak in run loggers.

PR #509 fixed the leak for the pipeline-level logger by calling close_logger()
in executor.run(). However, when user task code calls get_logger() inside a
task, plombery creates a *separate* task-scoped logger named
``plombery.{run_id}-{task_id}`` (see plombery.logger.get_logger). That logger
has its own FileHandler against logs.jsonl and was never closed, so 1 file
descriptor leaked per pipeline run. After enough runs the process hits the
OS soft limit (256 on macOS by default) and Plombery silently fails to accept
new connections.

This test reproduces the leak and verifies it is fixed: it runs a pipeline
many times in-process and asserts that
  (a) the file-descriptor count does not grow proportional to the number of
      runs (POSIX only — Windows uses num_handles() with different semantics
      and isn't a reliable signal), and
  (b) no plombery.* run logger retains an open FileHandler after the loop
      (checked on every platform).
"""

import gc
import logging
import sys
from asyncio import sleep

import psutil
import pytest

from plombery import _Plombery as Plombery
from plombery.orchestrator import run_pipeline_now

from .pipeline_1 import pipeline1


def _live_run_handlers():
    """Return (logger_name, handler) pairs for every plombery.* run logger
    that still holds an open FileHandler."""
    live = []
    for name, logger in logging.Logger.manager.loggerDict.items():
        if not isinstance(logger, logging.Logger):
            continue
        if not name.startswith("plombery."):
            continue
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                if (
                    getattr(handler, "stream", None) is not None
                    and not handler.stream.closed
                ):
                    live.append((name, handler))
    return live


@pytest.mark.asyncio
async def test_run_loggers_release_resources(app: Plombery):
    """After running a pipeline N times, no plombery.* run logger should
    still hold an open FileHandler, and (on POSIX) the process file-descriptor
    count should not grow proportional to the number of runs.

    The unfixed bug grows the FD count by ~1 per run via the task-scoped
    logger ``plombery.{run_id}-{task_id}``; 25 runs reliably exceed the
    steady-state threshold below.
    """
    app.start()
    app.register_pipeline(pipeline1)

    proc = psutil.Process()
    posix = sys.platform != "win32"
    gc.collect()
    fd_before = proc.num_fds() if posix else None

    n_runs = 25
    for _ in range(n_runs):
        await run_pipeline_now(pipeline1)

    await sleep(1)
    gc.collect()
    fd_after = proc.num_fds() if posix else None
    live = _live_run_handlers()

    assert not live, (
        f"Issue #491 regression: after {n_runs} runs, "
        f"live run-logger handlers = {[name for name, _ in live]}. "
        f"Expected no live handlers."
    )

    if posix:
        fd_delta = fd_after - fd_before
        assert fd_delta <= 2, (
            f"Issue #491 regression: after {n_runs} runs, "
            f"FD delta = {fd_delta} (before={fd_before}, after={fd_after}). "
            f"Expected FD delta <= 2."
        )

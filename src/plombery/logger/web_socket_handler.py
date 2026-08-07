import asyncio
import logging
import queue
from logging.handlers import QueueHandler, QueueListener
from typing import Optional

from plombery._internals.logging import logger as internal_logger
from plombery.logger.log_record import ExtendedLogRecord
from plombery.websocket import sio


# The event loop the Socket.IO server runs on.
#
# Log records are emitted from the QueueListener thread, but `sio` is an
# AsyncServer bound to the loop that serves the app: its coroutines have to be
# scheduled back onto that loop rather than run on a new one.
_server_loop: Optional[asyncio.AbstractEventLoop] = None


def bind_event_loop(loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
    """Remember the loop Socket.IO runs on. Called once, at startup."""

    global _server_loop

    try:
        _server_loop = loop or asyncio.get_running_loop()
    except RuntimeError:
        # Started outside an event loop: live logs stay disabled, the log file
        # is written all the same.
        _server_loop = None


class WebSocketHandler(logging.Handler):
    def emit(self, record: ExtendedLogRecord):
        loop = _server_loop

        if loop is None or loop.is_closed():
            return

        try:
            asyncio.run_coroutine_threadsafe(self._async_emit(record), loop)
        except RuntimeError as error:
            # The loop is shutting down: dropping a live log line is preferable
            # to breaking the listener thread, the line is on disk anyway.
            internal_logger.debug("Cannot stream a log line: %s", error)

    async def _async_emit(self, record: ExtendedLogRecord):
        await sio.emit(f"logs.{record.run_id}", record.message)


# Logs to be sent over the websocket are first added to a queue
# and from there are actually sent to the websocket
#
# From Dealing with handlers that block:
# https://docs.python.org/3/howto/logging-cookbook.html#dealing-with-handlers-that-block
_logs_queue = queue.Queue(-1)

handler = WebSocketHandler()
_listener = QueueListener(_logs_queue, handler)
_listener.start()


def build_queue_handler(formatter: logging.Formatter) -> QueueHandler:
    """A QueueHandler of its own for each logger, sharing the one queue.

    The formatter carries the pipeline, task and map index of the logger it
    belongs to, and QueueHandler formats the record as it enqueues it. Sharing
    a single handler would mean sharing its formatter, so concurrent tasks
    would label each other's log lines.
    """

    queue_handler = QueueHandler(_logs_queue)
    queue_handler.setFormatter(formatter)

    return queue_handler

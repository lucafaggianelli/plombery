import asyncio
import logging
import queue
from logging.handlers import QueueHandler, QueueListener

from plombery.logger.log_record import ExtendedLogRecord
from plombery.websocket import sio


class WebSocketHandler(logging.Handler):
    def emit(self, record: ExtendedLogRecord):
        asyncio.run(self._async_emit(record))

    async def _async_emit(self, record: ExtendedLogRecord):
        await sio.emit(f"logs.{record.run_id}", record.message)


# Logs to be sent over the websocket are first added to a queue
# and from there are actually sent to the websocket
#
# From Dealing with handlers that block:
# https://docs.python.org/3/howto/logging-cookbook.html#dealing-with-handlers-that-block
_logs_queue = queue.Queue(-1)
queue_handler = QueueHandler(_logs_queue)

handler = WebSocketHandler()
_listener = QueueListener(_logs_queue, handler)
_listener.start()

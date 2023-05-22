import asyncio
from logging.handlers import QueueHandler

from plombery.websocket import manager


class WebSocketHandler(QueueHandler):
    def __init__(self) -> None:
        super().__init__(manager)

    def enqueue(self, record):
        asyncio.create_task(manager.broadcast("logs", record.message))

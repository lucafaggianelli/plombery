from logging.handlers import QueueHandler

from plombery.websocket import manager


class WebSocketHandler(QueueHandler):
    def __init__(self, run_id: int) -> None:
        super().__init__(manager)

        self.run_id = run_id

    def enqueue(self, record):
        manager.emit(f"logs.{self.run_id}", record.message)

from logging import getLogger
from typing import Any, Dict, List, Set
from fastapi import WebSocket

from plombery.utils import run_all_coroutines


logger = getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

        # Unsubscribe from all subscriptions
        for sockets in self.subscriptions.values():
            try:
                sockets.remove(websocket)
            except KeyError:
                pass

    def subscribe(self, websocket: WebSocket, topic: str) -> None:
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()

        self.subscriptions[topic].add(websocket)

    def unsubscribe(self, websocket: WebSocket, topic: str) -> None:
        if topic not in self.subscriptions:
            return

        try:
            self.subscriptions[topic].remove(websocket)
        except KeyError:
            pass

    def emit(self, topic: str, data: Any):
        all_coroutines = []

        for connection in self.subscriptions.get(topic, set()):
            all_coroutines.append(
                connection.send_json(
                    {
                        "type": topic,
                        "data": data,
                    }
                )
            )

        run_all_coroutines(all_coroutines)

    def broadcast(self, type: str, data: Any):
        all_coroutines = []

        for connection in self.active_connections:
            all_coroutines.append(
                connection.send_json(
                    {
                        "type": type,
                        "data": data,
                    }
                )
            )

        run_all_coroutines(all_coroutines)

    async def handle_messages(self, websocket: WebSocket):
        data: dict = await websocket.receive_json()

        msg_type = data.get("type", None)
        payload = data.get("data", None)

        if msg_type == "subscribe":
            if payload:
                manager.subscribe(websocket, payload)
        elif msg_type == "unsubscribe":
            if payload:
                manager.unsubscribe(websocket, payload)
        else:
            logger.warning("Unknown message type %s", msg_type)


manager = ConnectionManager()

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from plombery.websocket import manager

router = APIRouter(prefix="/ws")


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await manager.handle_messages(websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

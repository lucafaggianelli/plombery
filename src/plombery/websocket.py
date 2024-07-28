import socketio


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
asgi = socketio.ASGIApp(socketio_server=sio)

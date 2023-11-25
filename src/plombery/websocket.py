from fastapi import FastAPI
import socketio


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


def install_socketio_server(app: FastAPI):
    return socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)

from fastapi import FastAPI

from plombery.api.authentication import init_auth
from plombery._version import __version__
from plombery.websocket import install_socketio_server
from .middlewares import SPAStaticFiles, setup_cors
from .routers import pipelines, runs


API_PREFIX = "/api"

app = FastAPI(title="Plombery", version=__version__, redirect_slashes=False)

setup_cors(app)
auth_router = init_auth(app)

app.include_router(pipelines.router, prefix=API_PREFIX)
app.include_router(runs.router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)

combined_app = install_socketio_server(app)

app.mount("/", SPAStaticFiles(api_prefix=API_PREFIX))

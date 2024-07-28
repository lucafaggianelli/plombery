from fastapi import FastAPI

from plombery.api.authentication import build_auth_router
from plombery._version import __version__
from plombery.websocket import asgi
from plombery.api.middlewares import SPAStaticFiles, setup_cors
from plombery.api.routers import pipelines, runs


API_PREFIX = "/api"

app = FastAPI(title="Plombery", version=__version__, redirect_slashes=False)

# Mount the websocket before the other middlewares
# to avoid conflicts
app.mount("/ws", asgi, name="socket")

setup_cors(app)

app.include_router(pipelines.router, prefix=API_PREFIX)
app.include_router(runs.router, prefix=API_PREFIX)
app.include_router(build_auth_router(app), prefix=API_PREFIX)

app.mount("/", SPAStaticFiles(api_prefix=API_PREFIX))

from fastapi import FastAPI

from plombery.api.authentication import init_auth
from plombery._version import __version__
from .middlewares import FRONTEND_FOLDER, SPAStaticFiles, setup_cors
from .routers import pipelines, runs, websocket


API_PREFIX = "/api"

app = FastAPI(title="Plombery", version=__version__, redirect_slashes=False)

setup_cors(app)
auth_router = init_auth(app)

app.include_router(pipelines.router, prefix=API_PREFIX)
app.include_router(runs.router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(websocket.router, prefix=API_PREFIX)

app.mount("/", SPAStaticFiles(directory=FRONTEND_FOLDER, html=True))

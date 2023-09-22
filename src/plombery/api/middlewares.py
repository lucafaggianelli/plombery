from pathlib import Path
from typing import Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from plombery.config import settings


FRONTEND_FOLDER = Path(__file__).parent.parent / "static"


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            else:
                raise ex


def setup_cors(app: FastAPI):
    origins: Sequence[str] = [
        str(settings.frontend_url).rstrip("/"),
    ]

    # Help during develop so the app can be opened at localhost or 127.0.0.1
    if settings.frontend_url.host == "localhost":
        origins.append(
            str(settings.frontend_url).replace("localhost", "127.0.0.1").rstrip("/")
        )
    elif settings.frontend_url.host == "127.0.0.1":
        origins.append(
            str(settings.frontend_url).replace("127.0.0.1", "localhost").rstrip("/")
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

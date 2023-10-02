from pathlib import Path
from typing import List

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
    origins: List[str] = []

    if settings.allowed_origins == "*":
        origins.append("*")
    else:
        origins = [str(origin) for origin in settings.allowed_origins]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

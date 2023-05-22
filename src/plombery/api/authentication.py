from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from plombery.config import settings


def init_auth(app: FastAPI):
    if not settings.auth:
        # If authentication is not enabled, register a
        # dummy endpoint to return an empty user

        @app.get("/whoami")
        async def get_current_user_no_auth(request: Request):
            return {
                "user": None,
                "is_authentication_enabled": False,
            }

        return

    app.add_middleware(SessionMiddleware, secret_key=settings.auth.secret_key.get_secret_value())

    oauth = OAuth()
    oauth.register(
        name="default",
        client_id=settings.auth.client_id.get_secret_value(),
        client_secret=settings.auth.client_secret.get_secret_value(),
        server_metadata_url=settings.auth.server_metadata_url,
        access_token_url=settings.auth.access_token_url,
        authorize_url=settings.auth.authorize_url,
        jwks_uri=settings.auth.jwks_uri,
        client_kwargs=settings.auth.client_kwargs,
    )

    @app.get("/login")
    async def login(request: Request):
        redirect_uri = request.url_for("auth_redirect")
        return await oauth.default.authorize_redirect(request, redirect_uri)

    @app.post("/logout")
    async def logout(request: Request):
        request.session.pop("user", None)

    @app.get("/whoami")
    async def get_current_user(request: Request):
        user = request.session.get("user")

        return {
            "user": user,
            "is_authentication_enabled": True,
        }

    @app.get("/redirect")
    async def auth_redirect(request: Request):
        token = await oauth.default.authorize_access_token(request)
        user = token["userinfo"]

        if user:
            request.session["user"] = dict(user)

        return RedirectResponse(url=settings.frontend_url)


async def _needs_auth(request: Request):
    if not settings.auth:
        return None

    user = request.session.get("user")

    if not user:
        raise HTTPException(401, "You must be authenticated to access this API route")

    return user


NeedsAuth = Depends(_needs_auth)

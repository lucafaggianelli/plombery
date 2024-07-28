from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from plombery.config import settings


def build_auth_router(app: FastAPI) -> APIRouter:
    router = APIRouter(
        prefix="/auth",
        tags=["Authentication"],
    )

    if not settings.auth:
        # If authentication is not enabled, register a
        # dummy endpoint to return an empty user

        @router.get("/whoami")
        async def get_current_user_no_auth(request: Request):
            return {
                "user": None,
                "is_authentication_enabled": False,
            }

        return router

    app.add_middleware(
        SessionMiddleware, secret_key=settings.auth.secret_key.get_secret_value()
    )

    # Explicitly convert URL objects to str as from Pydantic v2
    server_metadata_url = (
        str(settings.auth.server_metadata_url)
        if settings.auth.server_metadata_url
        else None
    )
    access_token_url = (
        str(settings.auth.access_token_url) if settings.auth.access_token_url else None
    )
    authorize_url = (
        str(settings.auth.authorize_url) if settings.auth.authorize_url else None
    )
    jwks_uri = str(settings.auth.jwks_uri) if settings.auth.jwks_uri else None

    oauth = OAuth()
    oauth.register(
        name="default",
        client_id=settings.auth.client_id.get_secret_value(),
        client_secret=settings.auth.client_secret.get_secret_value(),
        server_metadata_url=server_metadata_url,
        access_token_url=access_token_url,
        authorize_url=authorize_url,
        jwks_uri=jwks_uri,
        client_kwargs=settings.auth.client_kwargs,
    )

    if not oauth.default:
        raise ValueError("Error registering OAuth client")

    oauth_client: StarletteOAuth2App = oauth.default

    @router.get("/login")
    async def login(request: Request):
        redirect_uri = request.url_for("auth_redirect")
        return await oauth_client.authorize_redirect(request, redirect_uri)

    @router.post("/logout")
    async def logout(request: Request):
        request.session.pop("user", None)

    @router.get("/whoami")
    async def get_current_user(request: Request):
        user = request.session.get("user")

        return {
            "user": user,
            "is_authentication_enabled": True,
        }

    @router.get("/redirect")
    async def auth_redirect(request: Request):
        token = await oauth_client.authorize_access_token(request)
        user = token["userinfo"]

        if user:
            request.session["user"] = dict(user)

        return RedirectResponse(url=str(settings.frontend_url))

    return router


async def _needs_auth(request: Request):
    if not settings.auth:
        return None

    user = request.session.get("user")

    if not user:
        raise HTTPException(401, "You must be authenticated to access this API route")

    return user


NeedsAuth = Depends(_needs_auth)

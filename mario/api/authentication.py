from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware


def init_auth(app: FastAPI):
    app.add_middleware(SessionMiddleware, secret_key="secret-string")

    oauth = OAuth()
    oauth.register()

    @app.get("/login")
    async def login(request: Request):
        redirect_uri = request.url_for("auth_redirect")
        return await oauth.okta.authorize_redirect(request, redirect_uri)

    @app.post("/logout")
    async def logout(request: Request):
        request.session.pop("user", None)

    @app.get("/whoami")
    async def get_current_user(request: Request):
        user = request.session.get("user")

        if not user:
            raise HTTPException(401)

        return user

    @app.get("/redirect")
    async def auth_redirect(request: Request):
        token = await oauth.okta.authorize_access_token(request)
        user = token["userinfo"]

        if user:
            request.session["user"] = dict(user)

        return RedirectResponse(url="http://localhost:5173/")

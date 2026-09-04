from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import HttpUrl, SecretStr
import pytest

from plombery.api.authentication import build_auth_router
from plombery.config import settings
from plombery.config.model import AuthSettings


GOOGLE_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"
IDP_METADATA_URL = "https://idp.example.com/.well-known/openid-configuration"


@pytest.fixture
def build_auth():
    """Build the auth router against a given authentication configuration.

    `build_auth_router` reads the global settings and completes them with the
    provider preset, so the previous value is put back afterwards to keep the
    tests independent of each other.
    """

    previous = settings.auth

    def build(**kwargs) -> tuple[TestClient, AuthSettings]:
        settings.auth = AuthSettings(
            client_id=SecretStr("client-id"),
            client_secret=SecretStr("client-secret"),
            **kwargs,
        )

        app = FastAPI()
        app.include_router(build_auth_router(app), prefix="/api")

        return TestClient(app), settings.auth

    yield build

    settings.auth = previous


def test_a_preset_provider_fills_in_its_oauth_endpoints(build_auth):
    """Naming a provider is all the configuration a preset needs: the endpoints
    come from the preset, and without them Authlib has nothing to call."""

    _, auth = build_auth(provider="google")

    assert str(auth.server_metadata_url) == GOOGLE_METADATA_URL


def test_a_preset_provider_keeps_the_configured_client_kwargs(build_auth):
    """A preset only fills in what the configuration left out: the Google
    preset defines no `client_kwargs`, so the configured scope has to survive."""

    _, auth = build_auth(
        provider="google", client_kwargs={"scope": "openid email profile"}
    )

    assert str(auth.server_metadata_url) == GOOGLE_METADATA_URL
    assert auth.client_kwargs == {"scope": "openid email profile"}


@pytest.mark.parametrize(
    "kwargs, expected_in_url",
    [
        ({"provider": "google"}, "accounts.google.com"),
        (
            {"provider": "microsoft", "microsoft_tenant_id": "a-tenant"},
            "a-tenant",
        ),
    ],
)
def test_a_preset_provider_requests_a_scope(build_auth, kwargs, expected_in_url):
    """Naming a provider has to be enough to sign in. Without a scope the
    authorization URL carries no `nonce` either, so the provider returns no ID
    token and there is no user to put in the session."""

    _, auth = build_auth(**kwargs)

    assert expected_in_url in str(auth.server_metadata_url)
    assert auth.client_kwargs == {"scope": "openid email profile"}


def test_the_configuration_wins_over_the_preset(build_auth):
    _, auth = build_auth(
        provider="microsoft",
        server_metadata_url=HttpUrl(IDP_METADATA_URL),
        client_kwargs={"scope": "openid email profile User.Read"},
    )

    assert str(auth.server_metadata_url) == IDP_METADATA_URL
    assert auth.client_kwargs == {"scope": "openid email profile User.Read"}


def test_the_generic_provider_keeps_the_configured_endpoints(build_auth):
    """The generic provider describes a configuration that declares its own
    endpoints, so it must leave every one of them alone."""

    _, auth = build_auth(
        provider="generic",
        server_metadata_url=HttpUrl(IDP_METADATA_URL),
    )

    assert str(auth.server_metadata_url) == IDP_METADATA_URL


def test_a_configuration_without_a_provider_is_served_as_generic(build_auth):
    """`provider` is optional — a configuration can declare the OAuth endpoints
    itself. The login page still needs a provider to render a button for."""

    client, auth = build_auth(server_metadata_url=HttpUrl(IDP_METADATA_URL))

    assert str(auth.server_metadata_url) == IDP_METADATA_URL

    response = client.get("/api/auth/providers")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "generic", "name": "OAuth", "redirect_url": "/api/auth/redirect"}
    ]


def test_the_configured_provider_is_reported(build_auth):
    client, _ = build_auth(provider="google")

    response = client.get("/api/auth/providers")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "google", "name": "Google", "redirect_url": "/api/auth/redirect"}
    ]


def test_an_unsupported_provider_is_rejected(build_auth):
    with pytest.raises(ValueError, match="not-a-provider"):
        build_auth(provider="not-a-provider")


def test_whoami_reports_no_user_until_the_session_has_one(build_auth):
    client, _ = build_auth(provider="google")

    response = client.get("/api/auth/whoami")

    assert response.status_code == 200
    assert response.json() == {"user": None, "is_authentication_enabled": True}


def test_whoami_reports_that_authentication_is_disabled(build_auth):
    previous = settings.auth
    settings.auth = None

    try:
        app = FastAPI()
        app.include_router(build_auth_router(app), prefix="/api")
        response = TestClient(app).get("/api/auth/whoami")
    finally:
        settings.auth = previous

    assert response.status_code == 200
    assert response.json() == {"user": None, "is_authentication_enabled": False}

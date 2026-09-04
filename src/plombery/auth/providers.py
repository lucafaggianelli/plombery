from collections.abc import Callable

from plombery.config import settings
from plombery.config.model import AuthSettings


def _get_google(auth_settings: AuthSettings):
    return {
        "name": "Google",
        "metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
        "client_kwargs": {"scope": "openid email profile"},
    }


def _get_microsoft(auth_settings: AuthSettings):
    return {
        "name": "Microsoft",
        "metadata_url": f"https://login.microsoftonline.com/{auth_settings.microsoft_tenant_id or 'common'}/v2.0/.well-known/openid-configuration",
        "client_kwargs": {"scope": "openid email profile"},
    }


def _get_generic(auth_settings: AuthSettings):
    return {
        "name": "OAuth",
        "metadata_url": auth_settings.server_metadata_url,
        "client_kwargs": auth_settings.client_kwargs,
    }


_AUTH_PROVIDERS: dict[str, Callable[[AuthSettings], dict]] = {
    "google": _get_google,
    "microsoft": _get_microsoft,
    "generic": _get_generic,
}


def get_provider_config(provider_id: str):
    provider_fn = _AUTH_PROVIDERS.get(provider_id)

    if provider_fn and settings.auth:
        return provider_fn(settings.auth)

    return None

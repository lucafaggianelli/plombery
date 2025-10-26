from typing import Callable

from plombery.config.model import AuthSettings
from plombery.config import settings


def _get_google(settings: AuthSettings):
    return {
        "name": "Google",
        "metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
    }


def _get_microsoft(settings: AuthSettings):
    return {
        "name": "Microsoft",
        "metadata_url": f"https://login.microsoftonline.com/{settings.microsoft_tenant_id or 'common'}/v2.0/.well-known/openid-configuration",
        "client_kwargs": {"scope": "openid email profile"},
    }


_AUTH_PROVIDERS: dict[str, Callable[[AuthSettings], dict]] = {
    "google": _get_google,
    "microsoft": _get_microsoft,
}


def get_provider_config(provider_id: str):
    provider_fn = _AUTH_PROVIDERS.get(provider_id)

    if provider_fn and settings.auth:
        return provider_fn(settings.auth)

    return None

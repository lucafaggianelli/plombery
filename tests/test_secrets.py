import pytest
from pydantic import SecretStr, ValidationError

from plombery import BaseSecrets


class WarehouseSecrets(BaseSecrets):
    WAREHOUSE_URI: SecretStr


def test_resolves_from_a_prefixed_env_var(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PLOMBERY_SECRET_WAREHOUSE_URI", "postgres://user:pass@host/db")

    secrets = WarehouseSecrets()

    assert secrets.WAREHOUSE_URI.get_secret_value() == "postgres://user:pass@host/db"


def test_value_is_masked_in_repr(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PLOMBERY_SECRET_WAREHOUSE_URI", "postgres://user:pass@host/db")

    secrets = WarehouseSecrets()

    assert "pass" not in repr(secrets)
    assert "pass" not in str(secrets)


def test_a_missing_secret_fails_clearly(monkeypatch: pytest.MonkeyPatch):
    """A missing value must raise at construction, not resolve to None and
    fail later wherever the task happens to use it."""

    monkeypatch.delenv("PLOMBERY_SECRET_WAREHOUSE_URI", raising=False)

    with pytest.raises(ValidationError):
        WarehouseSecrets()

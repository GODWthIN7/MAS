import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.anyio
async def test_healthcheck() -> None:
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["environment"] == "development"


@pytest.mark.anyio
async def test_healthcheck_uses_environment_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("APP_NAME", "MAS Staging API")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9001")

    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["environment"] == "staging"
    assert app.title == "MAS Staging API"
    assert app.debug is True
    assert get_settings().port == 9001


def test_invalid_port_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "not-a-port")

    with pytest.raises(ValueError, match="PORT must be set to a valid integer value."):
        get_settings()


def test_invalid_debug_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEBUG", "ture")

    with pytest.raises(ValueError, match="DEBUG must be set to a valid boolean value."):
        get_settings()


@pytest.mark.parametrize("port", ["-1", "99999"])
def test_out_of_range_port_raises_clear_error(
    monkeypatch: pytest.MonkeyPatch,
    port: str,
) -> None:
    monkeypatch.setenv("PORT", port)

    with pytest.raises(ValueError, match="PORT must be between 1 and 65535."):
        get_settings()

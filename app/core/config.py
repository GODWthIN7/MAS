import os
from functools import lru_cache


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be set to a valid boolean value.")


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be set to a valid integer value.") from exc
    if not 1 <= port <= 65535:
        raise ValueError(f"{name} must be between 1 and 65535.")
    return port


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "MAS API")
        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = _get_bool("DEBUG", False)
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = _get_int("PORT", 8000)


@lru_cache
def get_settings() -> Settings:
    return Settings()

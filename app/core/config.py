import os
from functools import lru_cache


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be set to a valid integer value.") from exc


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

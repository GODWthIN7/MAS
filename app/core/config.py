import os
from functools import lru_cache


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "MAS API")
        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = _get_bool("DEBUG", False)
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))


@lru_cache
def get_settings() -> Settings:
    return Settings()

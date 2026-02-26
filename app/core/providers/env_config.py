from functools import lru_cache
from app.core.config.env_config import EnvConfig


@lru_cache()
def get_env_config() -> EnvConfig:
    """get environmet cofiguration

    Returns:
        EnvConfig
    """
    return EnvConfig()  # type: ignore

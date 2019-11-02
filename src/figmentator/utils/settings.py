"""
Encapsulate the configuration for figmentator
"""
from pydantic import BaseSettings


class _Settings(BaseSettings):
    """ The basic app settings that don't require Postgres """

    cache_url: str = "memory://"

    class Config:
        """ Additional configuration for the settings """

        env_prefix = "FIG_"


Settings = _Settings()

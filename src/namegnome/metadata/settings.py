# WARNING: This settings loader is for LOCAL DEVELOPMENT ONLY.
# Never commit your .env file or share your API keys.
# Ensure .env is listed in .gitignore!

"""Settings loader for metadata provider API keys.

Loads TMDB and TVDB credentials from environment variables or .env file.

Required .env keys:
- TMDB_API_KEY
- TMDB_READ_ACCESS_TOKEN (optional, for advanced usage)
- TVDB_API_KEY (optional, for TVDB client)
- TVDB_PIN (optional, for TVDB client)
"""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for metadata provider API keys.

    Loads TMDB and TVDB credentials from environment variables or .env file.
    """

    TMDB_API_KEY: str
    TMDB_READ_ACCESS_TOKEN: str | None = None
    TVDB_API_KEY: str | None = None
    TVDB_PIN: str | None = None
    OMDB_API_KEY: str | None = None

    model_config = ConfigDict(extra="allow")

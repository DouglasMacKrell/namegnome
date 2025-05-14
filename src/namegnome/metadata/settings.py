# WARNING: This settings loader is for LOCAL DEVELOPMENT ONLY.
# Never commit your .env file or share your API keys.
# Ensure .env is listed in .gitignore!

"""Settings loader for metadata provider API keys.

Loads TMDB, TVDB, OMDb, and Fanart.tv credentials from environment variables or
.env file.

Required .env keys:
- TMDB_API_KEY
- TMDB_READ_ACCESS_TOKEN (optional, for advanced usage)
- TVDB_API_KEY (optional, for TVDB client)
- TVDB_PIN (optional, for TVDB client)
- OMDB_API_KEY (optional, for OMDb client)
- FANARTTV_API_KEY (optional, for Fanart.tv client)
"""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class MissingAPIKeyError(Exception):
    """Raised when a required API key is missing from the environment or .env file."""

    def __init__(self, key: str) -> None:
        """Initialize the error with the missing key name."""
        super().__init__(
            f"Missing required API key: {key}\n"
            "See documentation: https://github.com/douglasmackrell/namegnome#provider-configuration"
        )
        self.key = key


class Settings(BaseSettings):
    """Settings for metadata provider API keys.

    Loads TMDB, TVDB, OMDb, and Fanart.tv credentials from environment
    variables or .env file.
    """

    TMDB_API_KEY: str
    TMDB_READ_ACCESS_TOKEN: str | None = None
    TVDB_API_KEY: str | None = None
    TVDB_PIN: str | None = None
    OMDB_API_KEY: str | None = None
    FANARTTV_API_KEY: str | None = None

    model_config = ConfigDict(extra="allow")

    def require_keys(self) -> None:
        """Raise MissingAPIKeyError if any required key is missing."""
        required = ["TMDB_API_KEY"]
        for key in required:
            if not getattr(self, key, None):
                raise MissingAPIKeyError(key)

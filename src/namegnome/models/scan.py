"""Scan options and related models."""

from pathlib import Path
from typing import List, Optional, Set

from pydantic import BaseModel, Field

from namegnome.models.core import MediaType


class ScanOptions(BaseModel):
    """Options for scanning media files."""

    root: Path
    """Root directory to scan."""

    media_types: List[MediaType] = Field(default_factory=list)
    """Types of media to scan for."""

    platform: str = "plex"
    """Platform name (e.g., 'plex', 'jellyfin')."""

    verify_hash: bool = False
    """Whether to verify file hashes."""

    recursive: bool = True
    """Whether to scan subdirectories recursively."""

    include_hidden: bool = False
    """Whether to include hidden files and directories."""

    show_name: Optional[str] = None
    """Explicit show name for TV files."""

    movie_year: Optional[int] = None
    """Explicit year for movie files."""

    anthology: bool = False
    """Whether the TV show is an anthology series."""

    adjust_episodes: bool = False
    """Adjust episode numbering for incorrectly numbered files."""

    json_output: bool = False
    """Output results in JSON format."""

    llm_model: Optional[str] = None
    """LLM model to use for fuzzy matching."""

    no_color: bool = False
    """Disable colored output."""

    strict_directory_structure: bool = True
    """Enforce platform directory structure."""

    target_extensions: Set[str] = Field(default_factory=set)

    class Config:
        """Pydantic config for ScanOptions."""

        arbitrary_types_allowed = True

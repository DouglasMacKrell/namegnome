"""Scan options and related models.

This module defines the configuration options for scanning media files in
namegnome.
- Used to parameterize directory scans for different platforms, media types, and
  user preferences.
- Ensures all options are explicit and validated for reproducibility and
  cross-platform correctness.
- Designed for extensibility and integration with CLI/LLM workflows (see
  PLANNING.md and README.md).

Design:
- ScanOptions encapsulates all user- and platform-facing scan parameters, with
  sensible defaults for safety and usability.
- Supports advanced features like LLM-based fuzzy matching, strict directory
  enforcement, and hash verification.
"""

from pathlib import Path
from typing import List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field

from namegnome.models.core import MediaType


class ScanOptions(BaseModel):
    """Options for scanning media files.

    Encapsulates all configuration parameters for a media scan session.
    Used by the scanner, CLI, and planner to control scan behavior and output.
    """

    root: Path
    """Root directory to scan (must be absolute for safety and reproducibility)."""

    media_types: List[MediaType] = Field(default_factory=list)
    """Types of media to scan for (TV, movie, music, etc.)."""

    platform: str = "plex"
    """Platform name (e.g., 'plex', 'jellyfin'). Determines rule set and directory
    structure."""

    verify_hash: bool = False
    """Whether to verify file hashes (enables integrity checks and duplicate
    detection)."""

    recursive: bool = True
    """Whether to scan subdirectories recursively (default True for full library
    scans)."""

    include_hidden: bool = False
    """Whether to include hidden files and directories (default False for
    safety)."""

    show_name: Optional[str] = None
    """Explicit show name for TV files (overrides filename parsing if set)."""

    movie_year: Optional[int] = None
    """Explicit year for movie files (overrides filename parsing if set)."""

    anthology: bool = False
    """Whether the TV show is an anthology series (enables special episode handling)."""

    adjust_episodes: bool = False
    """Adjust episode numbering for incorrectly numbered files (for legacy/poorly
    tagged libraries)."""

    json_output: bool = False
    """Output results in JSON format (for scripting/automation)."""

    llm_model: Optional[str] = None
    """LLM model to use for fuzzy matching (enables AI-assisted disambiguation)."""

    no_color: bool = False
    """Disable colored output (for CI/logging environments)."""

    strict_directory_structure: bool = True
    """Enforce platform directory structure (prevents accidental misplacement;
    see PLANNING.md)."""

    target_extensions: Set[str] = Field(default_factory=set)
    """Set of file extensions to include in the scan (empty means all supported
    types)."""

    # ---------------------------------------------------------------------
    # Additional CLI flags (added in Sprint 0.4)
    # ---------------------------------------------------------------------

    untrusted_titles: bool = False
    """Allow title extraction from untrusted sources (filename heuristics)."""

    max_duration: Optional[int] = None
    """Maximum media duration in minutes; used to skip oversized matches."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

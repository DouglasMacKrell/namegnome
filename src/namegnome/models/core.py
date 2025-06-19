"""Core domain models for namegnome.

This module defines the foundational data structures for media file scanning,
classification, and planning.
- Used throughout namegnome for representing media files, scan results, and plan
  statuses.
- Ensures all file paths are absolute for safety and cross-platform correctness.
- Designed for extensibility, auditability, and backward compatibility (see
  PLANNING.md and README.md).

Design:
- MediaType and PlanStatus enums provide clear, type-safe status and
  classification for all workflows.
- MediaFile encapsulates all metadata needed for renaming, hashing, and external
  lookups.
- ScanResult aggregates scan output and supports conversion to a plan skeleton.
- Backward compatibility fields ensure older plan/scan files remain valid as the
  schema evolves.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

# Avoid circular imports with TYPE_CHECKING
if TYPE_CHECKING:
    from namegnome.models.plan import RenamePlan


class MediaType(str, Enum):
    """Type of media file.

    Used to classify files as TV, movie, music, or unknown for rule selection and
    reporting.
    """

    TV = "tv"
    MOVIE = "movie"
    MUSIC = "music"
    UNKNOWN = "unknown"


class PlanStatus(str, Enum):
    """Status of a rename plan item.

    Used to track the lifecycle of each rename/move operation (pending, moved,
    skipped, etc.).
    """

    PENDING = "pending"
    MOVED = "moved"
    SKIPPED = "skipped"
    CONFLICT = "conflict"
    FAILED = "failed"
    MANUAL = "manual"


class MediaFile(BaseModel):
    """Represents a media file discovered during scanning.

    Encapsulates all metadata needed for renaming, hashing, and external lookups.
    Used as the atomic unit for scan results and rename plans.
    """

    path: Path
    """Absolute path to the file. Must be absolute for safety and cross-platform
    correctness."""

    size: int
    """Size of the file in bytes (for reporting and duplicate detection)."""

    media_type: MediaType
    """Type of media file (TV, movie, music, unknown)."""

    modified_date: datetime
    """Last modified date of the file (for audit and sorting)."""

    season: Optional[int] = None
    """Season number for TV shows (if applicable)."""

    episode: Optional[int] = None
    """Episode number for TV shows (if applicable)."""

    episode_title: Optional[str] = None
    """Title of the episode (if parsed or provided by metadata)."""

    year: Optional[int] = None
    """Release year for movies (if available)."""

    title: Optional[str] = None
    """Title of the show or movie (parsed or from metadata)."""

    hash: Optional[str] = None
    """SHA-256 hash of the file, if computed (for integrity and duplicate
    detection)."""

    metadata_ids: Dict[str, str] = Field(default_factory=dict)
    """IDs from external metadata providers, e.g., {'tmdb': '12345'} (for
    enrichment and lookups)."""

    def root_relative_path(self: "MediaFile", root_dir: Path) -> str:
        """Get the path relative to the root directory.

        Args:
            root_dir: The root directory to make the path relative to.

        Returns:
            The relative path as a string.
        """
        try:
            return str(self.path.relative_to(root_dir))
        except ValueError:
            # If the path is not relative to the root, return the full path
            return str(self.path)

    @model_validator(mode="after")
    def validate_path(self: "MediaFile") -> "MediaFile":
        """Ensure the path is absolute.

        Returns:
            MediaFile: The validated object.

        Raises:
            ValueError: If the path is not absolute.
        """
        # Reason: Absolute paths are required to prevent accidental relative moves
        # and ensure cross-platform correctness.
        if not self.path.is_absolute():
            raise ValueError(f"Path must be absolute: {self.path}")
        return self


class ScanResult(BaseModel):
    """Result of a media scan operation.

    Aggregates all files and metadata discovered during a scan. Supports
    conversion to a plan skeleton. Backward compatibility fields ensure older
    scan files remain valid as schema evolves (see PLANNING.md).
    """

    files: List[MediaFile]
    """List of media files discovered in the scan."""

    root_dir: Path
    """Root directory of the scan (absolute path)."""

    media_types: List[MediaType]
    """Types of media scanned for (TV, movie, music, etc.)."""

    platform: str
    """Platform name (e.g., 'plex', 'jellyfin') for rule selection."""

    scan_time: datetime = Field(default_factory=datetime.now)
    """When the scan was run (timestamp for audit/logging)."""

    # Backward compatibility fields
    total_files: int = 0
    """Total number of files examined (for backward compatibility with older scan
    files)."""

    skipped_files: int = 0
    """Number of files skipped (for backward compatibility with older scan
    files)."""

    by_media_type: Dict[MediaType, int] = Field(default_factory=dict)
    """Count of files by media type (for backward compatibility with older scan
    files)."""

    scan_duration_seconds: float = 0.0
    """Duration of the scan in seconds (for backward compatibility with older
    scan files)."""

    errors: List[str] = Field(default_factory=list)
    """List of errors encountered during the scan (for backward compatibility
    with older scan files)."""

    # Alias for backward compatibility
    @property
    def media_files(self: "ScanResult") -> List[MediaFile]:
        """Alias for files (for backward compatibility)."""
        return self.files

    def as_plan(
        self: "ScanResult",
        plan_id: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> "RenamePlan":
        """Convert scan result to a rename plan skeleton.

        Args:
            plan_id: Optional plan ID to use, defaults to timestamp-based ID
            platform: Optional platform override, defaults to self.platform

        Returns:
            A rename plan with no items (to be filled in by planner).
        """
        from namegnome.models.plan import RenamePlan

        return RenamePlan(
            id=(
                plan_id
                if plan_id is not None
                else datetime.now().strftime("%Y%m%d_%H%M%S")
            ),
            created_at=datetime.now(),
            root_dir=self.root_dir,
            platform=(platform if platform is not None else self.platform),
            media_types=self.media_types,
            items=[],
        )

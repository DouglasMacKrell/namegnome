"""Core domain models for namegnome."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

# Avoid circular imports with TYPE_CHECKING
if TYPE_CHECKING:
    from namegnome.models.plan import RenamePlan


class MediaType(str, Enum):
    """Type of media file."""

    TV = "tv"
    MOVIE = "movie"
    MUSIC = "music"
    UNKNOWN = "unknown"


class PlanStatus(str, Enum):
    """Status of a rename plan item."""

    PENDING = "pending"
    MOVED = "moved"
    SKIPPED = "skipped"
    CONFLICT = "conflict"
    FAILED = "failed"
    MANUAL = "manual"


class MediaFile(BaseModel):
    """Represents a media file discovered during scanning."""

    path: Path
    """Absolute path to the file."""

    size: int
    """Size of the file in bytes."""

    media_type: MediaType
    """Type of media file."""

    modified_date: datetime
    """Last modified date of the file."""

    season: Optional[int] = None
    """Season number for TV shows."""

    episode: Optional[int] = None
    """Episode number for TV shows."""

    year: Optional[int] = None
    """Release year for movies."""

    title: Optional[str] = None
    """Title of the show or movie."""

    hash: Optional[str] = None
    """SHA-256 hash of the file, if computed."""

    metadata_ids: Dict[str, str] = Field(default_factory=dict)
    """IDs from external metadata providers, e.g., {'tmdb': '12345'}."""

    def root_relative_path(self, root_dir: Path) -> str:
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
        """Ensure the path is absolute."""
        if not self.path.is_absolute():
            raise ValueError(f"Path must be absolute: {self.path}")
        return self


class ScanResult(BaseModel):
    """Result of a media scan operation."""

    files: List[MediaFile]
    """List of media files discovered."""

    root_dir: Path
    """Root directory of the scan."""

    media_types: List[MediaType]
    """Types of media scanned for."""

    platform: str
    """Platform name (e.g., 'plex', 'jellyfin')."""

    scan_time: datetime = Field(default_factory=datetime.now)
    """When the scan was run."""

    # Backward compatibility fields
    total_files: int = 0
    """Total number of files examined (for backward compatibility)."""

    skipped_files: int = 0
    """Number of files skipped (for backward compatibility)."""

    by_media_type: Dict[MediaType, int] = Field(default_factory=dict)
    """Count of files by media type (for backward compatibility)."""

    scan_duration_seconds: float = 0.0
    """Duration of the scan in seconds (for backward compatibility)."""

    errors: List[str] = Field(default_factory=list)
    """List of errors encountered during the scan (for backward compatibility)."""

    # Alias for backward compatibility
    @property
    def media_files(self: "ScanResult") -> List[MediaFile]:
        """Alias for files (for backward compatibility)."""
        return self.files

    def as_plan(
        self: "ScanResult", plan_id: Optional[str] = None, platform: Optional[str] = None
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
            platform=(
                platform 
                if platform is not None 
                else self.platform
            ),
            media_types=self.media_types,
            items=[],
        )

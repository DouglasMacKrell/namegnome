"""Core domain models for namegnome."""

from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator


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
    
    media_type: MediaType = MediaType.UNKNOWN
    """Type of media detected."""
    
    modified_date: datetime
    """Last modification date of the file."""
    
    hash: Optional[str] = None
    """Optional SHA-256 hash of the file, if --verify was specified."""

    metadata_ids: Dict[str, str] = Field(default_factory=dict)
    """Dictionary of provider IDs for the file (e.g., {"tmdb": "12345"})."""

    @model_validator(mode="after")
    def ensure_absolute_path(self) -> "MediaFile":
        """Ensure path is absolute."""
        if not self.path.is_absolute():
            raise ValueError("Path must be absolute")
        return self


class RenamePlanItem(BaseModel):
    """A single file rename/move operation."""
    
    source: Path
    """Absolute source path."""
    
    destination: Path
    """Absolute destination path."""
    
    media_file: MediaFile
    """Original media file reference."""
    
    status: PlanStatus = PlanStatus.PENDING
    """Current status of this rename operation."""
    
    reason: Optional[str] = None
    """Reason for failure or conflict, if applicable."""
    
    manual: bool = False
    """Whether this item requires manual confirmation."""
    
    manual_reason: Optional[str] = None
    """Reason why manual confirmation is required."""

    @model_validator(mode="after")
    def ensure_absolute_paths(self) -> "RenamePlanItem":
        """Ensure both paths are absolute."""
        if not self.source.is_absolute() or not self.destination.is_absolute():
            raise ValueError("Paths must be absolute")
        return self


class RenamePlan(BaseModel):
    """A collection of rename operations to be executed together."""
    
    id: str = Field(...)
    """Unique identifier for this plan."""
    
    created_at: datetime = Field(default_factory=datetime.now)
    """When this plan was created."""
    
    root_dir: Path
    """Root directory that was scanned."""
    
    items: List[RenamePlanItem] = Field(default_factory=list)
    """List of rename operations in this plan."""
    
    platform: str
    """Target platform (e.g., 'plex', 'jellyfin')."""
    
    media_types: List[MediaType] = Field(default_factory=list)
    """Types of media found in this plan."""
    
    metadata_providers: List[str] = Field(default_factory=list)
    """Metadata providers used for this plan."""
    
    llm_model: Optional[str] = None
    """LLM model used for fuzzy matching, if applicable."""


class ScanResult(BaseModel):
    """Summary result of scanning a directory."""
    
    total_files: int = 0
    """Total number of files found."""
    
    media_files: List[MediaFile] = Field(default_factory=list)
    """List of media files found."""
    
    skipped_files: int = 0
    """Number of files skipped (non-media or ignored)."""
    
    by_media_type: Dict[MediaType, int] = Field(default_factory=dict)
    """Counts per media type."""
    
    errors: List[str] = Field(default_factory=list)
    """List of errors encountered during scan."""
    
    scan_duration_seconds: float = 0.0
    """Duration of the scan in seconds."""
    
    root_dir: Path
    """Root directory that was scanned."""

    def as_plan(self, plan_id: str, platform: str) -> RenamePlan:
        """Convert scan result to an empty rename plan."""
        return RenamePlan(
            id=plan_id,
            root_dir=self.root_dir,
            platform=platform,
            media_types=list({mf.media_type for mf in self.media_files}),
            items=[],
        ) 
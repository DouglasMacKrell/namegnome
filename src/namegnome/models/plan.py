"""Models for rename plans."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from namegnome.models.core import MediaFile, MediaType, PlanStatus


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
    def validate_paths(self: "RenamePlanItem") -> "RenamePlanItem":
        """Ensure the paths are absolute."""
        if not self.source.is_absolute():
            raise ValueError(f"Source path must be absolute: {self.source}")
        if not self.destination.is_absolute():
            raise ValueError(f"Destination path must be absolute: {self.destination}")
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

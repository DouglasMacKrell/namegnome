"""Models for rename plans.

This module defines the data structures for representing file rename/move plans in
namegnome.
- Used to serialize, validate, and audit planned file operations before execution.
- Ensures all paths are absolute for safety and cross-platform correctness.
- Designed for extensibility and reproducibility (see PLANNING.md and README.md).

Design:
- Each plan is a collection of atomic rename/move operations, with metadata for
  audit and undo/redo.
- Plans are validated for absolute paths to prevent accidental relative moves (see
  validator).
- Supports tracking of manual interventions, platform-specific logic, and LLM-based
  fuzzy matching.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from namegnome.models.core import MediaFile, MediaType, PlanStatus

# Re-export PlanStatus for external callers (deprecated import path)
__all__: list[str] = [
    "RenamePlanItem",
    "RenamePlan",
    "PlanStatus",
]


class RenamePlanItem(BaseModel):
    """A single file rename/move operation in a plan.

    Represents one atomic file operation, including source/destination, media
    metadata, and status. Used for both dry-run previews and actual execution.
    """

    source: Path
    """Absolute source path of the file to be renamed/moved."""

    destination: Path
    """Absolute destination path for the file after renaming/move."""

    media_file: MediaFile
    """Reference to the original media file and its parsed metadata."""

    status: PlanStatus = PlanStatus.PENDING
    """Current status of this rename operation (pending, done, failed, etc.)."""

    reason: Optional[str] = None
    """Reason for failure or conflict, if applicable (set after execution attempt)."""

    manual: bool = False
    """Whether this item requires manual confirmation (e.g., ambiguous match,
    conflict)."""

    manual_reason: Optional[str] = None
    """Reason why manual confirmation is required (e.g., fuzzy match, user
    override)."""

    episode_title: Optional[str] = "Unknown Title"
    episode: Optional[str] = None

    @model_validator(mode="after")
    def validate_paths(self: "RenamePlanItem") -> "RenamePlanItem":
        """Ensure the source and destination paths are absolute.

        Returns:
            RenamePlanItem: The validated item.

        Raises:
            ValueError: If either path is not absolute.
        """
        # Reason: Absolute paths are required to prevent accidental relative moves
        # and ensure cross-platform correctness.
        if not self.source.is_absolute():
            raise ValueError(f"Source path must be absolute: {self.source}")
        if not self.destination.is_absolute():
            raise ValueError(f"Destination path must be absolute: {self.destination}")
        return self


class RenamePlan(BaseModel):
    """A collection of rename operations to be executed together as a plan.

    Encapsulates all metadata and operations for a single renaming session. Used
    for audit, undo/redo, and reproducibility (see plan_store and PLANNING.md).
    """

    id: str = Field(...)
    """Unique identifier for this plan (UUID, used for storage and audit)."""

    created_at: datetime = Field(default_factory=datetime.now)
    """Timestamp when this plan was created (for audit/logging)."""

    root_dir: Path
    """Root directory that was scanned to generate this plan."""

    items: List[RenamePlanItem] = Field(default_factory=list)
    """List of all rename/move operations in this plan."""

    platform: str
    """Target platform for naming rules (e.g., 'plex', 'jellyfin')."""

    media_types: List[MediaType] = Field(default_factory=list)
    """Types of media found in this plan (movies, shows, etc.)."""

    metadata_providers: List[str] = Field(default_factory=list)
    """Metadata providers used to enrich this plan (e.g., TMDb, TVDb)."""

    llm_model: Optional[str] = None
    """LLM model used for fuzzy matching or disambiguation, if applicable."""


# ---------------------------------------------------------------------------
# Backwards-compatibility exports (tests still import PlanStatus from this module)
# ---------------------------------------------------------------------------

__all__: list[str] = [
    "RenamePlanItem",
    "RenamePlan",
    "PlanStatus",
]

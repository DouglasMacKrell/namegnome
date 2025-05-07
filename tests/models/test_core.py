"""Tests for the core models module."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from namegnome.models.core import (
    MediaFile,
    MediaType,
    PlanStatus,
    ScanResult,
)
from namegnome.models.plan import RenamePlan, RenamePlanItem


class TestMediaType:
    """Tests for the MediaType enum."""

    def test_enum_values(self) -> None:
        """Test the expected enum values exist."""
        assert MediaType.TV.value == "tv"
        assert MediaType.MOVIE.value == "movie"
        assert MediaType.MUSIC.value == "music"
        assert MediaType.UNKNOWN.value == "unknown"

    def test_serialization(self) -> None:
        """Test MediaType serializes to string in JSON."""
        media_file = MediaFile(
            path=Path("/tmp/test.mp4").absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )
        json_data = media_file.model_dump_json()
        parsed = json.loads(json_data)
        assert parsed["media_type"] == "tv"


class TestPlanStatus:
    """Tests for the PlanStatus enum."""

    def test_enum_values(self) -> None:
        """Test the expected enum values exist."""
        assert PlanStatus.PENDING.value == "pending"
        assert PlanStatus.MOVED.value == "moved"
        assert PlanStatus.SKIPPED.value == "skipped"
        assert PlanStatus.CONFLICT.value == "conflict"
        assert PlanStatus.FAILED.value == "failed"
        assert PlanStatus.MANUAL.value == "manual"


class TestMediaFile:
    """Tests for the MediaFile model."""

    def test_create_valid(self) -> None:
        """Test creating a valid MediaFile instance."""
        media_file = MediaFile(
            path=Path("/tmp/test.mp4").absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )
        assert media_file.path.is_absolute()
        assert media_file.size == 1024
        assert media_file.media_type == MediaType.TV
        assert media_file.hash is None
        assert media_file.metadata_ids == {}

    def test_relative_path_raises(self) -> None:
        """Test that relative paths are rejected."""
        with pytest.raises(ValidationError):
            MediaFile(
                path=Path("relative/path.mp4"),
                size=1024,
                media_type=MediaType.TV,
                modified_date=datetime.now(),
            )

    def test_serialization_roundtrip(self) -> None:
        """Test serialization and deserialization."""
        now = datetime.now()
        original = MediaFile(
            path=Path("/tmp/test.mp4").absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=now,
            hash="abc123",
            metadata_ids={"tmdb": "12345"},
        )

        json_data = original.model_dump_json()

        # Manual check of JSON structure
        parsed = json.loads(json_data)
        assert parsed["path"] == str(Path("/tmp/test.mp4").absolute())
        assert parsed["size"] == 1024
        assert parsed["media_type"] == "tv"
        assert parsed["hash"] == "abc123"
        assert parsed["metadata_ids"] == {"tmdb": "12345"}

        # Convert back to model and verify
        model_dict = original.model_dump()
        reconstructed = MediaFile.model_validate(model_dict)

        assert reconstructed.path == original.path
        assert reconstructed.size == original.size
        assert reconstructed.media_type == original.media_type
        assert reconstructed.hash == original.hash
        assert reconstructed.metadata_ids == original.metadata_ids


class TestRenamePlanItem:
    """Tests for the RenamePlanItem model."""

    @pytest.fixture
    def media_file(self) -> MediaFile:
        """Create a sample MediaFile for tests."""
        return MediaFile(
            path=Path("/tmp/source.mp4").absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )

    def test_create_valid(self, media_file: MediaFile) -> None:
        """Test creating a valid RenamePlanItem."""
        item = RenamePlanItem(
            source=Path("/tmp/source.mp4").absolute(),
            destination=Path("/tmp/destination.mp4").absolute(),
            media_file=media_file,
        )
        assert item.source.is_absolute()
        assert item.destination.is_absolute()
        assert item.status == PlanStatus.PENDING
        assert item.manual is False
        assert item.reason is None

    def test_relative_paths_raises(self, media_file: MediaFile) -> None:
        """Test that relative paths are rejected."""
        with pytest.raises(ValidationError):
            RenamePlanItem(
                source=Path("relative/source.mp4"),
                destination=Path("/absolute/dest.mp4").absolute(),
                media_file=media_file,
            )

        with pytest.raises(ValidationError):
            RenamePlanItem(
                source=Path("/absolute/source.mp4").absolute(),
                destination=Path("relative/dest.mp4"),
                media_file=media_file,
            )

    def test_manual_with_reason(self, media_file: MediaFile) -> None:
        """Test setting manual flag with a reason."""
        item = RenamePlanItem(
            source=Path("/tmp/source.mp4").absolute(),
            destination=Path("/tmp/destination.mp4").absolute(),
            media_file=media_file,
            manual=True,
            manual_reason="Needs review",
        )
        assert item.manual is True
        assert item.manual_reason == "Needs review"
        assert item.status == PlanStatus.PENDING

    def test_failed_status_with_reason(self, media_file: MediaFile) -> None:
        """Test setting failed status with a reason."""
        item = RenamePlanItem(
            source=Path("/tmp/source.mp4").absolute(),
            destination=Path("/tmp/destination.mp4").absolute(),
            media_file=media_file,
            status=PlanStatus.FAILED,
            reason="Destination already exists",
        )
        assert item.status == PlanStatus.FAILED
        assert item.reason == "Destination already exists"


class TestRenamePlan:
    """Tests for the RenamePlan model."""

    @pytest.fixture
    def media_file(self) -> MediaFile:
        """Create a sample MediaFile for tests."""
        return MediaFile(
            path=Path("/tmp/source.mp4").absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )

    @pytest.fixture
    def plan_item(self, media_file: MediaFile) -> RenamePlanItem:
        """Create a sample RenamePlanItem for tests."""
        return RenamePlanItem(
            source=Path("/tmp/source.mp4").absolute(),
            destination=Path("/tmp/destination.mp4").absolute(),
            media_file=media_file,
        )

    def test_create_valid(self, plan_item: RenamePlanItem) -> None:
        """Test creating a valid RenamePlan."""
        plan = RenamePlan(
            id="plan-123",
            root_dir=Path("/tmp").absolute(),
            platform="plex",
            items=[plan_item],
            media_types=[MediaType.TV],
        )
        assert plan.id == "plan-123"
        assert plan.root_dir == Path("/tmp").absolute()
        assert plan.platform == "plex"
        assert len(plan.items) == 1
        assert plan.items[0] == plan_item
        assert plan.media_types == [MediaType.TV]
        assert plan.metadata_providers == []
        assert plan.llm_model is None

    def test_serialization_roundtrip(self, plan_item: RenamePlanItem) -> None:
        """Test serialization and deserialization of RenamePlan."""
        now = datetime.now()
        plan = RenamePlan(
            id="plan-123",
            created_at=now,
            root_dir=Path("/tmp").absolute(),
            platform="plex",
            items=[plan_item],
            media_types=[MediaType.TV, MediaType.MOVIE],
            metadata_providers=["tmdb", "tvdb"],
            llm_model="deepseek-coder",
        )

        # Serialize to dict
        plan_dict = plan.model_dump()

        # Deserialize back to RenamePlan
        reconstructed = RenamePlan.model_validate(plan_dict)

        assert reconstructed.id == plan.id
        assert reconstructed.created_at == plan.created_at
        assert reconstructed.root_dir == plan.root_dir
        assert reconstructed.platform == plan.platform
        assert len(reconstructed.items) == len(plan.items)
        assert reconstructed.media_types == plan.media_types
        assert reconstructed.metadata_providers == plan.metadata_providers
        assert reconstructed.llm_model == plan.llm_model


class TestScanResult:
    """Tests for the ScanResult model."""

    @pytest.fixture
    def media_file(self) -> MediaFile:
        """Create a sample MediaFile for tests."""
        return MediaFile(
            path=Path("/tmp/show.mp4").absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )

    @pytest.fixture
    def movie_file(self) -> MediaFile:
        """Create a sample MediaFile for tests."""
        return MediaFile(
            path=Path("/tmp/movie.mp4").absolute(),
            size=1024,
            media_type=MediaType.MOVIE,
            modified_date=datetime.now(),
        )

    def test_create_valid(self, media_file: MediaFile, movie_file: MediaFile) -> None:
        """Test creating a valid ScanResult."""
        result = ScanResult(
            files=[media_file, movie_file],
            media_types=[MediaType.TV, MediaType.MOVIE],
            platform="plex",
            root_dir=Path("/tmp").absolute(),
            # Backward compatibility fields
            total_files=10,
            skipped_files=8,
            by_media_type={
                MediaType.TV: 1,
                MediaType.MOVIE: 1,
            },
            errors=["Some error occurred"],
            scan_duration_seconds=1.5,
        )

        assert len(result.files) == 2
        assert result.root_dir == Path("/tmp").absolute()
        assert len(result.media_types) == 2
        assert result.platform == "plex"
        assert result.total_files == 10
        assert result.skipped_files == 8
        assert len(result.errors) == 1
        assert result.scan_duration_seconds == 1.5

    def test_as_plan(self, media_file: MediaFile, movie_file: MediaFile) -> None:
        """Test converting ScanResult to RenamePlan."""
        result = ScanResult(
            files=[media_file, movie_file],
            media_types=[MediaType.TV, MediaType.MOVIE],
            platform="plex",
            root_dir=Path("/tmp").absolute(),
            # Backward compatibility fields
            total_files=10,
            skipped_files=8,
            by_media_type={
                MediaType.TV: 1,
                MediaType.MOVIE: 1,
            },
            scan_duration_seconds=1.5,
        )

        plan = result.as_plan()
        assert plan.root_dir == Path("/tmp").absolute()
        assert len(plan.items) == 0  # Initially empty
        assert plan.platform == "plex"
        assert plan.media_types == [MediaType.TV, MediaType.MOVIE]

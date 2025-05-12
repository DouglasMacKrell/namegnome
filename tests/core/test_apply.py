"""Tests for the namegnome.core.apply module.

This test suite covers:
- Transactional application of rename plans
- Hash verification after move
- Rollback on failure
- Skipping identical files

See TASK.md Sprint 1.2 for required scenarios.
"""

from datetime import datetime, timezone
from pathlib import Path

from namegnome.core.apply import apply_plan
from namegnome.models.core import MediaFile, MediaType, PlanStatus
from namegnome.models.plan import RenamePlan, RenamePlanItem
from namegnome.utils.hash import sha256sum


def test_apply_plan_successful_move_and_hash(tmp_path: Path) -> None:
    """Test apply_plan moves a file and verifies hash successfully."""
    # Create a source file with known content
    src = tmp_path / "source.txt"
    content = b"test123"
    src.write_bytes(content)
    src_hash = sha256sum(src)

    # Destination path
    dst = tmp_path / "dest.txt"

    # Build MediaFile and RenamePlanItem
    media_file = MediaFile(
        path=src,
        size=len(content),
        media_type=MediaType.MOVIE,
        modified_date=datetime.now(timezone.utc),
        hash=src_hash,
    )
    item = RenamePlanItem(
        source=src,
        destination=dst,
        media_file=media_file,
    )
    plan = RenamePlan(
        id="test",
        created_at=datetime.now(timezone.utc),
        root_dir=tmp_path,
        items=[item],
        platform="plex",
        media_types=[MediaType.MOVIE],
        metadata_providers=[],
    )

    # Run apply_plan
    result = apply_plan(plan, verify_hash=True)

    # Check result
    assert result.success
    assert result.moved == 1
    assert result.failed == 0
    assert result.skipped == 0
    assert not result.failures
    # Check file was moved
    assert not src.exists()
    assert dst.exists()
    # Check hash matches
    assert sha256sum(dst) == src_hash
    # Check status updated
    assert plan.items[0].status == PlanStatus.MOVED


def test_apply_plan_hash_mismatch_failure(tmp_path: Path) -> None:
    """Test apply_plan fails and marks item as FAILED if hash does not match after move."""
    # Create a source file with known content
    src = tmp_path / "source.txt"
    content = b"original"
    src.write_bytes(content)
    src_hash = sha256sum(src)

    # Destination path
    dst = tmp_path / "dest.txt"

    # Build MediaFile and RenamePlanItem
    media_file = MediaFile(
        path=src,
        size=len(content),
        media_type=MediaType.MOVIE,
        modified_date=datetime.now(timezone.utc),
        hash=src_hash,
    )
    item = RenamePlanItem(
        source=src,
        destination=dst,
        media_file=media_file,
    )
    plan = RenamePlan(
        id="test",
        created_at=datetime.now(timezone.utc),
        root_dir=tmp_path,
        items=[item],
        platform="plex",
        media_types=[MediaType.MOVIE],
        metadata_providers=[],
    )

    # Patch atomic_move to corrupt the destination after move
    from namegnome.core import apply as apply_mod

    orig_atomic_move = apply_mod.atomic_move

    def corrupting_move(
        src: Path, dst: Path, dry_run: bool = False, overwrite: bool = False
    ) -> None:
        orig_atomic_move(src, dst, dry_run=dry_run, overwrite=overwrite)
        # Corrupt the destination file after move
        dst.write_bytes(b"corrupted")

    apply_mod.atomic_move = corrupting_move

    try:
        result = apply_plan(plan, verify_hash=True)
        assert not result.success
        assert result.failed == 1
        assert plan.items[0].status == PlanStatus.FAILED
        assert result.failures == [plan.items[0]]
    finally:
        apply_mod.atomic_move = orig_atomic_move


def test_apply_plan_skip_identical(tmp_path: Path) -> None:
    """Test apply_plan skips move if destination exists and hash matches (skip-identical logic)."""
    # Create a source file with known content
    src = tmp_path / "source.txt"
    content = b"identical"
    src.write_bytes(content)
    src_hash = sha256sum(src)

    # Create destination file with identical content
    dst = tmp_path / "dest.txt"
    dst.write_bytes(content)
    assert sha256sum(dst) == src_hash

    # Build MediaFile and RenamePlanItem
    media_file = MediaFile(
        path=src,
        size=len(content),
        media_type=MediaType.MOVIE,
        modified_date=datetime.now(timezone.utc),
        hash=src_hash,
    )
    item = RenamePlanItem(
        source=src,
        destination=dst,
        media_file=media_file,
    )
    plan = RenamePlan(
        id="test",
        created_at=datetime.now(timezone.utc),
        root_dir=tmp_path,
        items=[item],
        platform="plex",
        media_types=[MediaType.MOVIE],
        metadata_providers=[],
    )

    # Run apply_plan with skip_identical=True
    result = apply_plan(plan, verify_hash=True, skip_identical=True)

    # Check result
    assert result.success
    assert result.skipped == 1
    assert result.moved == 0
    assert result.failed == 0
    assert not result.failures
    # Check files are unchanged
    assert src.exists()
    assert dst.exists()
    # Check status updated
    assert plan.items[0].status == PlanStatus.SKIPPED

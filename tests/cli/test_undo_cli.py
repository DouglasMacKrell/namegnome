"""CLI tests for the undo command."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from namegnome.cli.commands import app
from namegnome.models.core import MediaFile, MediaType
from namegnome.models.plan import RenamePlan, RenamePlanItem
from namegnome.utils.hash import sha256sum
from namegnome.utils.json import DateTimeEncoder

runner = CliRunner()


def test_undo_cli_yes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test undo CLI with --yes skips confirmation and restores file."""
    # Create original file
    src = tmp_path / "original.txt"
    content = b"cli-undo"
    src.write_bytes(content)
    src_hash = sha256sum(src)

    # Simulate move
    dst = tmp_path / "moved.txt"
    src.rename(dst)
    assert not src.exists()
    assert dst.exists()
    assert sha256sum(dst) == src_hash

    # Build plan and save to ~/.namegnome/plans
    from namegnome.utils.plan_store import _ensure_plan_dir

    plans_dir = _ensure_plan_dir()
    plan_id = "testcliundo"
    plan_path = plans_dir / f"{plan_id}.json"
    media_file = MediaFile(
        path=dst,
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
        id=plan_id,
        created_at=datetime.now(timezone.utc),
        root_dir=tmp_path,
        items=[item],
        platform="plex",
        media_types=[MediaType.MOVIE],
        metadata_providers=[],
    )
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2, cls=DateTimeEncoder)

    # Run CLI undo with --yes
    result = runner.invoke(app, ["undo", plan_id, "--yes"])
    assert result.exit_code == 0
    assert src.exists()
    assert not dst.exists()
    assert sha256sum(src) == src_hash
    assert "Undo completed for plan" in result.output


def test_undo_cli_confirmation_cancel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test undo CLI asks for confirmation and cancels if user says no."""
    # Create original file and plan as in the previous test
    src = tmp_path / "original2.txt"
    content = b"cli-undo2"
    src.write_bytes(content)
    src_hash = sha256sum(src)
    dst = tmp_path / "moved2.txt"
    src.rename(dst)
    from namegnome.utils.plan_store import _ensure_plan_dir

    plans_dir = _ensure_plan_dir()
    plan_id = "testcliundo2"
    plan_path = plans_dir / f"{plan_id}.json"
    media_file = MediaFile(
        path=dst,
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
        id=plan_id,
        created_at=datetime.now(timezone.utc),
        root_dir=tmp_path,
        items=[item],
        platform="plex",
        media_types=[MediaType.MOVIE],
        metadata_providers=[],
    )
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2, cls=DateTimeEncoder)

    # Simulate user input 'n' to cancel
    result = runner.invoke(app, ["undo", plan_id], input="n\n")
    assert result.exit_code == 1
    assert "Undo cancelled by user" in result.output
    # File should not be restored
    assert not src.exists()
    assert dst.exists()


def test_undo_cli_source_exists(tmp_path: Path) -> None:
    """Test undo CLI fails gracefully if source file already exists."""
    # Create original file and plan as in the previous test
    src = tmp_path / "original3.txt"
    content = b"cli-undo3"
    src.write_bytes(content)
    src_hash = sha256sum(src)
    dst = tmp_path / "moved3.txt"
    src.rename(dst)
    # Now recreate the source file (simulate user manually restoring it)
    src.write_bytes(b"different-content")
    from namegnome.utils.plan_store import _ensure_plan_dir

    plans_dir = _ensure_plan_dir()
    plan_id = "testcliundo3"
    plan_path = plans_dir / f"{plan_id}.json"
    media_file = MediaFile(
        path=dst,
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
        id=plan_id,
        created_at=datetime.now(timezone.utc),
        root_dir=tmp_path,
        items=[item],
        platform="plex",
        media_types=[MediaType.MOVIE],
        metadata_providers=[],
    )
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2, cls=DateTimeEncoder)

    # Run CLI undo with --yes
    result = runner.invoke(app, ["undo", plan_id, "--yes"])
    assert result.exit_code == 1
    assert (
        "already exists" in result.output or "cannot restore" in result.output.lower()
    )
    # File should not be overwritten
    assert src.read_bytes() == b"different-content"
    assert dst.exists()


def test_undo_cli_already_undone(tmp_path: Path) -> None:
    """Test undo CLI fails gracefully if destination is missing and source already exists (already undone)."""
    # Create original file and plan as in the previous test
    src = tmp_path / "original4.txt"
    content = b"cli-undo4"
    src.write_bytes(content)
    src_hash = sha256sum(src)
    dst = tmp_path / "moved4.txt"
    # Do NOT move src to dst; simulate already undone (src exists, dst missing)
    from namegnome.utils.plan_store import _ensure_plan_dir

    plans_dir = _ensure_plan_dir()
    plan_id = "testcliundo4"
    plan_path = plans_dir / f"{plan_id}.json"
    media_file = MediaFile(
        path=dst,
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
        id=plan_id,
        created_at=datetime.now(timezone.utc),
        root_dir=tmp_path,
        items=[item],
        platform="plex",
        media_types=[MediaType.MOVIE],
        metadata_providers=[],
    )
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2, cls=DateTimeEncoder)

    # Run CLI undo with --yes
    result = runner.invoke(app, ["undo", plan_id, "--yes"])
    assert result.exit_code == 1
    assert (
        "destination file does not exist" in result.output.lower()
        or "cannot restore" in result.output.lower()
    )
    # File should not be modified
    assert src.read_bytes() == content
    assert not dst.exists()


def test_undo_cli_multifile(tmp_path: Path) -> None:
    """Integration test: undo CLI restores multiple files in a plan."""
    # Create multiple files
    files = []
    hashes = []
    for i in range(3):
        src = tmp_path / f"file{i}.txt"
        content = f"multi-{i}".encode()
        src.write_bytes(content)
        files.append((src, content))
        hashes.append(sha256sum(src))
    # Move all files to new locations
    moved = []
    for i, (src, content) in enumerate(files):
        dst = tmp_path / f"moved{i}.txt"
        src.rename(dst)
        moved.append(dst)
    # Build multi-item plan and save to ~/.namegnome/plans
    from namegnome.utils.plan_store import _ensure_plan_dir

    plans_dir = _ensure_plan_dir()
    plan_id = "testclimultifile"
    plan_path = plans_dir / f"{plan_id}.json"
    items = []
    for i in range(3):
        media_file = MediaFile(
            path=moved[i],
            size=len(files[i][1]),
            media_type=MediaType.MOVIE,
            modified_date=datetime.now(timezone.utc),
            hash=hashes[i],
        )
        item = RenamePlanItem(
            source=files[i][0],
            destination=moved[i],
            media_file=media_file,
        )
        items.append(item)
    plan = RenamePlan(
        id=plan_id,
        created_at=datetime.now(timezone.utc),
        root_dir=tmp_path,
        items=items,
        platform="plex",
        media_types=[MediaType.MOVIE],
        metadata_providers=[],
    )
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2, cls=DateTimeEncoder)
    # Run CLI undo with --yes
    result = runner.invoke(app, ["undo", plan_id, "--yes"])
    assert result.exit_code == 0
    # All files should be restored and hashes match
    for i, (src, content) in enumerate(files):
        assert src.exists()
        assert sha256sum(src) == hashes[i]
        assert not moved[i].exists()
    assert "Undo completed for plan" in result.output

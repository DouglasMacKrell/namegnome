"""Tests for the namegnome.core.undo module.

This test suite covers:
- Transactional undo of rename plans
- Hash verification after undo
- CLI integration and confirmation logic

See TASK.md Sprint 1.2 for required scenarios.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from namegnome.core.undo import undo_plan
from namegnome.models.core import MediaFile, MediaType
from namegnome.models.plan import RenamePlan, RenamePlanItem
from namegnome.utils.hash import sha256sum
from namegnome.utils.json import DateTimeEncoder


def test_undo_plan_successful(tmp_path: Path) -> None:
    """Test undo_plan restores a file to its original location with correct hash."""
    # Create original file (A)
    src = tmp_path / "original.txt"
    content = b"undo-test"
    src.write_bytes(content)
    src_hash = sha256sum(src)

    # Simulate move to B
    dst = tmp_path / "moved.txt"
    src.rename(dst)
    assert not src.exists()
    assert dst.exists()
    assert sha256sum(dst) == src_hash

    # Build plan JSON (as if this move was done by apply_plan)
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
        id="undo-test",
        created_at=datetime.now(timezone.utc),
        root_dir=tmp_path,
        items=[item],
        platform="plex",
        media_types=[MediaType.MOVIE],
        metadata_providers=[],
    )
    plan_path = tmp_path / "plan.json"
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2, cls=DateTimeEncoder)

    # Call undo_plan
    undo_plan(plan_path)

    # Check file is restored to original location
    assert src.exists()
    assert not dst.exists()
    assert sha256sum(src) == src_hash

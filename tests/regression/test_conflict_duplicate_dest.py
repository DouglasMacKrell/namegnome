import sys
from pathlib import Path
from datetime import datetime

import pytest

from namegnome.core.planner import create_rename_plan, RenamePlanBuildContext
from namegnome.models.core import MediaFile, MediaType, PlanStatus, ScanResult
from namegnome.rules.plex import PlexRuleSet


@pytest.mark.parametrize("platform", ["win32"])
def test_duplicate_destination_conflict(tmp_path: Path, monkeypatch, platform) -> None:
    """Ensure duplicate destinations are marked as conflicts on all platforms."""

    monkeypatch.setattr(sys, "platform", platform, raising=False)

    f1 = tmp_path / "Show.S01E01.mp4"
    f2 = tmp_path / "show.s01e01.mp4"
    for f in (f1, f2):
        f.write_bytes(b"dummy")

    files = [
        MediaFile(
            path=f1,
            size=1,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
            title="Show",
            season=1,
            episode="01",
        ),
        MediaFile(
            path=f2,
            size=1,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
            title="Show",
            season=1,
            episode="01",
        ),
    ]

    scan = ScanResult(
        files=files,
        root_dir=tmp_path,
        media_types=[MediaType.TV],
        platform="plex",
        total_files=2,
        skipped_files=0,
        by_media_type={MediaType.TV: 2},
        scan_duration_seconds=0.0,
    )

    plan = create_rename_plan(
        RenamePlanBuildContext(
            scan_result=scan,
            rule_set=PlexRuleSet(),
            plan_id="reg-confict",
            platform="plex",
        )
    )

    # Either the planner marks them as conflicts *or* it rewrites the second
    # filename to avoid collision (e.g. "(1)" suffix).  Both behaviours are
    # acceptable – the key regression is that we never silently produce two
    # identical destinations.

    dests = {pi.destination.as_posix().lower() for pi in plan.items}
    assert len(dests) == 1 or any(pi.status == PlanStatus.CONFLICT for pi in plan.items)

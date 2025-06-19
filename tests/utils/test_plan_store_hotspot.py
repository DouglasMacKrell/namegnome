"""Tests for namegnome.utils.plan_store save/load functions."""

from datetime import datetime

import pytest

from namegnome.models.core import MediaType
from namegnome.models.plan import RenamePlan
from namegnome.models.scan import ScanOptions
from namegnome.utils import plan_store as ps


@pytest.fixture()
def isolated_home(tmp_path, monkeypatch):
    """Redirect HOME to a tmp directory so plan files are sandboxed."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # Windows CI sometimes uses USERPROFILE
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return tmp_path


def _dummy_plan(tmp_path):
    plan = RenamePlan(
        id="testplan",
        created_at=datetime.now(),
        root_dir=tmp_path,
        items=[],
        platform="plex",
        media_types=[MediaType.TV],
        metadata_providers=[],
        llm_model=None,
    )
    return plan


def _dummy_scan_options(tmp_path):
    return ScanOptions(root=tmp_path, media_types=[MediaType.TV])


def test_save_and_load_plan(isolated_home, tmp_path):
    plan = _dummy_plan(tmp_path)
    scan_opts = _dummy_scan_options(tmp_path)

    plan_id = ps.save_plan(plan, scan_opts, extra_args={"verify": False})
    # The function returns the generated UUID, not the plan.id we passed
    assert isinstance(plan_id, str) and len(plan_id) >= 8

    # Ensure plan and metadata files exist in the sandboxed directory
    plans_dir = isolated_home / ".namegnome" / "plans"
    json_path = plans_dir / f"{plan_id}.json"
    meta_path = plans_dir / f"{plan_id}.meta.yaml"
    assert json_path.exists() and meta_path.exists()

    # load_plan should round-trip the same plan data
    loaded_plan, metadata = ps.load_plan(plan_id)
    assert loaded_plan.id == plan.id  # original id preserved inside JSON
    assert metadata.id == plan_id


def test_get_latest_plan_id(isolated_home, tmp_path):
    plan = _dummy_plan(tmp_path)
    scan_opts = _dummy_scan_options(tmp_path)
    plan_id = ps.save_plan(plan, scan_opts)

    latest = ps.get_latest_plan_id()
    assert latest == plan_id

    # list_plans should return at least one tuple with our ID
    plans = ps.list_plans()
    ids = [pid for pid, _ in plans]
    assert plan_id in ids

    # get_plan_metadata returns RunMetadata
    meta = ps.get_plan_metadata(plan_id)
    assert meta.id == plan_id

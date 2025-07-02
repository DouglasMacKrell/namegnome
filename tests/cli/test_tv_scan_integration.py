# tests/cli/test_tv_scan_integration.py

import json
import shutil
import subprocess
from pathlib import Path


def test_scan_tv_integration(tmp_path: Path) -> None:
    """End-to-end CLI test: scan TV library emits rename plan JSON.

    This is the acceptance test for *Sprint 1.4 CLI TV Integration Happy Path*.

    Expectations:
    1. Running the CLI on the fixture library exits with code 0.
    2. A ``plan.json`` file is created in the working directory.
    3. The file contains valid JSON with required top-level keys.
    4. **No** output is written to *stderr* (the process is quiet on success).
    """

    # ------------------------------------------------------------------
    # 1. Arrange – copy fixture TV tree into tmpdir ---------------------
    # ------------------------------------------------------------------
    fixture_root = Path(__file__).parent.parent / "mocks" / "tv"
    # We copy instead of symlinking to ensure the scanner can freely walk
    # the directory on all CI platforms (Windows lacks symlink privileges
    # by default for non-admin accounts).
    library_path = tmp_path / "library"
    shutil.copytree(fixture_root, library_path)

    # Working directory must be inside *tmp_path* so the CLI will write
    # plan.json to an isolated location.
    workdir = tmp_path / "work"
    workdir.mkdir()

    # ------------------------------------------------------------------
    # 2. Act – invoke the CLI via subprocess ---------------------------
    # ------------------------------------------------------------------
    cmd = [
        "python",
        "-m",
        "namegnome",
        "scan",
        str(library_path),  # root path
        "--media-type",
        "tv",
        "--json",
        "-o",
        "plan.json",
    ]

    result = subprocess.run(  # noqa: S603 – test input, S607 – no shell
        cmd,
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
    )

    # ------------------------------------------------------------------
    # 3. Assert – validate process and output --------------------------
    # ------------------------------------------------------------------
    assert result.returncode == 0, result.stderr
    assert result.stderr == "", "CLI should not emit stderr on success"

    plan_path = workdir / "plan.json"
    assert plan_path.exists(), "plan.json should be created"

    data = json.loads(plan_path.read_text())
    # Basic schema sanity checks
    assert "items" in data, "plan JSON must contain 'items' key"
    assert "root_dir" in data, "plan JSON must contain 'root_dir' key"
    assert isinstance(data["items"], list), "'items' must be a list"

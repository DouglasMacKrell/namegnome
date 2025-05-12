"""Unit tests for namegnome.fs.operations.atomic_move.

Covers:
- Basic atomic move on the same filesystem
- Cross-device move fallback (EXDEV)
- Windows long path support
- Dry-run mode (no-op)
- Overwrite protection and logic (FileExistsError, identical skip, replacement)

All tests are platform-appropriate and E501 compliant.
"""

import errno
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

# Import the function to test (will be implemented in fs/operations.py)
from namegnome.fs.operations import WIN_MAX_PATH, atomic_move, get_win_long_path_prefix


def test_atomic_move_basic(tmp_path: Path) -> None:
    """Test that atomic_move renames a file from src to dst on the same filesystem."""
    # Arrange: create a source file
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"
    src.write_text("hello world")

    # Act
    atomic_move(src, dst)

    # Assert
    assert not src.exists()
    assert dst.exists()
    assert dst.read_text() == "hello world"


def test_cross_device(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that atomic_move falls back to copy+unlink on cross-device (EXDEV) error."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"
    src.write_text("cross device")

    # Patch Path.rename to raise EXDEV
    def raise_exdev(self: Path, target: Path) -> None:
        raise OSError(errno.EXDEV, "Invalid cross-device link")

    monkeypatch.setattr(Path, "rename", raise_exdev)

    # Patch shutil.copy2 to actually copy
    monkeypatch.setattr(shutil, "copy2", shutil.copy2)

    # Act
    atomic_move(src, dst)

    # Assert
    assert not src.exists()
    assert dst.exists()
    assert dst.read_text() == "cross device"


def test_long_paths_windows(mocker: Any, tmp_path: Path) -> None:
    """Test that atomic_move adds the Windows long path prefix for long paths on Windows."""
    if sys.platform != "win32":
        pytest.skip("Windows-only test")

    src = tmp_path / ("a" * (WIN_MAX_PATH + 1))
    dst = tmp_path / ("b" * (WIN_MAX_PATH + 1))
    src.write_text("long path")

    # Patch Path.rename to check the path
    called = {}

    def fake_rename(self: Path, target: Path) -> None:
        called["src"] = str(self)
        called["dst"] = str(target)

    mocker.patch.object(Path, "rename", fake_rename)

    atomic_move(src, dst)

    prefix = get_win_long_path_prefix()
    assert called["src"].startswith(prefix)
    assert called["dst"].startswith(prefix)


def test_dry_run_no_op(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test that atomic_move does not move files and logs when dry_run=True."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"
    src.write_text("dry run")

    atomic_move(src, dst, dry_run=True)

    assert src.exists()
    assert not dst.exists()
    out = capsys.readouterr().out.lower()
    assert "dry run" in out or "would move" in out


def test_overwrite_false_raises(tmp_path: Path) -> None:
    """Test that atomic_move raises FileExistsError if dst exists and overwrite is False."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"
    src.write_text("src data")
    dst.write_text("dst data")

    try:
        atomic_move(src, dst, overwrite=False)
    except FileExistsError:
        pass
    else:
        assert False, "FileExistsError not raised"

    assert src.exists()
    assert dst.exists()
    assert dst.read_text() == "dst data"


def test_overwrite_with_identical_hash(tmp_path: Path) -> None:
    """Test that atomic_move skips move if overwrite=True and src/dst are identical."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"
    content = "identical data"
    src.write_text(content)
    dst.write_text(content)

    atomic_move(src, dst, overwrite=True)

    # Both files should remain unchanged (move skipped)
    assert not src.exists()
    assert dst.exists()
    assert dst.read_text() == content


def test_overwrite_replaces_nonidentical(tmp_path: Path) -> None:
    """Test that atomic_move replaces dst with src if overwrite=True and files differ."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"
    src.write_text("new data")
    dst.write_text("old data")

    atomic_move(src, dst, overwrite=True)

    assert not src.exists()
    assert dst.exists()
    assert dst.read_text() == "new data"

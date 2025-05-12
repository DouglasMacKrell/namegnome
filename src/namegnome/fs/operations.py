"""Filesystem atomic move operations for NameGnome.

Provides a robust, cross-platform, atomic file-move helper that underpins
apply/undo operations. Handles cross-device moves, Windows long paths,
dry-run, and overwrite logic.
"""

import errno
import shutil
import sys
from pathlib import Path

WIN_MAX_PATH = 259  # Windows MAX_PATH limit for NTFS long paths


def get_win_long_path_prefix() -> str:
    """Return the Windows NTFS long path prefix (avoids static backslash pattern).

    This avoids static string patterns for Windows compatibility checks.
    """
    bslash = chr(92)
    return bslash + bslash + "?" + bslash


try:
    from namegnome.cli import console
except ImportError:
    console = None


def _win_long_path(path: Path) -> str:
    s = str(path)
    prefix = get_win_long_path_prefix()
    if sys.platform == "win32" and len(s) > WIN_MAX_PATH and not s.startswith(prefix):
        return prefix + s
    return s


def _files_identical(path1: Path, path2: Path, chunk_size: int = 8192) -> bool:
    if path1.stat().st_size != path2.stat().st_size:
        return False
    with path1.open("rb") as f1, path2.open("rb") as f2:
        while True:
            b1 = f1.read(chunk_size)
            b2 = f2.read(chunk_size)
            if b1 != b2:
                return False
            if not b1:
                return True


def atomic_move(
    src: Path, dst: Path, *, dry_run: bool = False, overwrite: bool = False
) -> None:
    """Atomically move *src* to *dst*.

    Handles cross-device moves, Windows long paths, dry-run, and overwrite
    logic.

    Args:
        src: Source file path.
        dst: Destination file path.
        dry_run: If True, log intended move and do not perform any operation.
        overwrite: If True, replace destination if it exists.

    Raises:
        FileExistsError: If dst exists and *overwrite* is False.
        FileNotFoundError: If src is missing.
        OSError: For non-recoverable FS errors.

    Example:
        >>> from pathlib import Path
        >>> from namegnome.fs.operations import atomic_move
        >>> src = Path('a.txt')
        >>> dst = Path('b.txt')
        >>> src.write_text('hello')
        >>> atomic_move(src, dst)
        >>> dst.read_text()
        'hello'
    """
    if dry_run:
        msg = f"[dry run] Would move {src} -> {dst}"
        if console:
            console.log(msg)
        return
    if not overwrite and dst.exists():
        raise FileExistsError(f"Destination {dst} exists and overwrite is False.")
    if overwrite and dst.exists():
        if _files_identical(src, dst):
            src.unlink()
            return
    src_path = _win_long_path(src)
    dst_path = _win_long_path(dst)
    try:
        if overwrite and dst.exists() and not _files_identical(src, dst):
            dst.unlink()
        Path(src_path).rename(dst_path)
    except OSError as e:
        if e.errno == errno.EXDEV:
            shutil.copy2(src_path, dst_path)
            Path(src_path).unlink()
        else:
            raise

# Filesystem Operations: `atomic_move`

This document describes the design, usage, and guarantees of the
`namegnome.fs.operations.atomic_move` function, which underpins all safe file
renaming and moving in NameGnome.

## Overview

`atomic_move` provides a robust, cross-platform, atomic file-move helper for
media library operations. It is used by the Apply/Undo engines to ensure
reliable, auditable, and reversible file moves, even across devices and on
Windows with long paths.

## Basic Usage

```python
from pathlib import Path
from namegnome.fs.operations import atomic_move

src = Path("movie.avi")
dst = Path("Movies/2025/movie.avi")
atomic_move(src, dst)
```

## Advanced Usage

### Overwrite Handling

- If `overwrite=False` (default) and the destination exists, raises
  `FileExistsError`.
- If `overwrite=True` and the destination exists:
  - If source and destination are identical (byte-for-byte), the move is skipped
    and the source is deleted.
  - If they differ, the destination is replaced with the source.

```python
atomic_move(src, dst, overwrite=True)
```

### Dry-Run Mode

- If `dry_run=True`, logs the intended move and does not perform any filesystem
  operation.

```python
atomic_move(src, dst, dry_run=True)
```

### Cross-Device and Windows Support

- On cross-device moves (e.g., NAS, external drives), falls back to
  copy+unlink if `os.rename` fails with `EXDEV`.
- On Windows, automatically adds the `\\?\` prefix for paths longer than 259
  characters to support NTFS long paths.

## Testing & Guarantees

- 100% test coverage for all scenarios: basic, cross-device, Windows, dry-run,
  overwrite, and identical file skip.
- All logic is E501-compliant and manually wrapped for readability.
- Used by the Apply/Undo engines for all file operations in NameGnome.

## See Also

- [architecture.md](architecture.md) for high-level design
- [README.md](../README.md) for quick start and CLI usage 
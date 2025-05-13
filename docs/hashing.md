# Hashing & Integrity: SHA-256 in NameGnome

This document explains the design, usage, and guarantees of NameGnome's
SHA-256 hashing utility. Hashing is central to file integrity, duplicate
skipping, and safe renaming in all core workflows.

## Purpose

- **Integrity verification:** Ensures files are not corrupted or altered during
  moves.
- **Duplicate detection:** Skips moves when the source and destination are
  byte-for-byte identical, saving time and preventing unnecessary writes.
- **Auditability:** Hashes are stored in plan files for later verification and
  rollback.

## How It Works

NameGnome uses a single utility function:

```python
from namegnome.utils.hash import sha256sum
```

- Computes the SHA-256 hash of a file, reading in 8MB chunks for efficiency.
- Used in scan, apply, and undo workflows.
- Returns a hex string (64 characters).

### Example: Python Usage

```python
from pathlib import Path
from namegnome.utils.hash import sha256sum

path = Path("movie.mkv")
hash_value = sha256sum(path)
print(f"SHA-256: {hash_value}")
```

### Example: CLI Usage

- `--verify` flag on `scan` and `apply` commands computes and stores hashes.
- During `apply`, hashes are checked after each move if `--verify` is enabled.
- If the destination hash does not match the source, the move is marked as
  failed and rollback is triggered (see [apply-undo.md](apply-undo.md)).

## Skip-Identical Logic

- If `skip_identical` is enabled (default in most workflows), and the
  destination file exists with the same hash as the source, the move is
  skipped and the item is marked as `SKIPPED`.
- This prevents unnecessary file operations and speeds up large batch renames.

## Design Rationale

- **SHA-256** is chosen for its collision resistance and wide support.
- Chunked reading (8MB) balances speed and memory usage for large files.
- Hashes are always computed in binary mode for cross-platform consistency.
- All hash logic is E501-wrapped and follows Google-style docstring/comment
  standards.

## Testing & Guarantees

- 100% test coverage for hash utility, including:
  - Good copy (hash matches after move)
  - Corrupted copy (hash mismatch triggers failure)
  - Identical destination (move skipped)
- Hashing is tested in both unit and integration tests (see
  [integration-testing.md](integration-testing.md)).

## See Also

- [apply-undo.md](apply-undo.md): How hashing integrates with apply/undo
- [fs-operations.md](fs-operations.md): Atomic file moves
- [README.md](../README.md): CLI usage and quick start 
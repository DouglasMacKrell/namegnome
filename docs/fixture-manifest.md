# Fixture Manifest Format Documentation

This document details the structure and format of the fixture manifest used by NameGnome's regression test suite.

## Overview

The fixture manifest (`tests/mocks/tv/fixture_manifest.yaml`) is a YAML file that defines the expected behavior and metadata for all test files in the regression suite. It serves as the ground truth for test validation and ensures consistent test behavior across different environments.

## File Structure

### Location
```
tests/mocks/tv/fixture_manifest.yaml
```

### Format
The manifest is a YAML array of objects, where each object describes a single test file:

```yaml
- file: "relative/path/to/test/file.mp4"
  field1: value1
  field2: value2
  # ... additional fields
```

## Required Fields

### `file`
- **Type**: String
- **Required**: Yes
- **Description**: Relative path to the test file from the `tests/mocks/tv/` directory
- **Example**: `"Paw Patrol/Paw Patrol-S01E01-Pups And The Kitty Tastrophe Pups Save A Train.mp4"`

### `status`
- **Type**: String (enum)
- **Required**: Yes
- **Values**: `auto`, `manual`, `unsupported`
- **Description**: Expected processing status for the file
  - `auto`: File should be processed automatically with high confidence
  - `manual`: File requires manual review (medium confidence)
  - `unsupported`: File cannot be processed (low confidence)

## Optional Fields

### `anthology`
- **Type**: Boolean
- **Required**: No
- **Default**: `false`
- **Description**: Whether the file contains multiple episodes (anthology format)
- **Example**: `true`

### `season`
- **Type**: Integer
- **Required**: No
- **Description**: Season number for the episodes
- **Example**: `1`

### `episodes`
- **Type**: Array of integers
- **Required**: No
- **Description**: List of episode numbers contained in the file
- **Examples**:
  - `[1]` (single episode)
  - `[5, 6]` (multi-episode span)
  - `[1, 2, 3]` (anthology with multiple episodes)

### `title_trusted`
- **Type**: Boolean
- **Required**: No
- **Default**: `true`
- **Description**: Whether the episode titles in the filename should be trusted
- **Example**: `false`

### `show_name`
- **Type**: String
- **Required**: No
- **Description**: Expected show name for the file
- **Example**: `"Paw Patrol"`

### `expected_confidence`
- **Type**: Float
- **Required**: No
- **Range**: 0.0 to 1.0
- **Description**: Expected confidence score for the file processing
- **Example**: `0.85`

### `reason`
- **Type**: String
- **Required**: No
- **Description**: Reason for the expected status (especially for manual/unsupported files)
- **Example**: `"Ambiguous episode titles"`

## Example Entries

### Auto-processed File
```yaml
- file: "Paw Patrol/Paw Patrol-S01E01-Pups And The Kitty Tastrophe Pups Save A Train.mp4"
  anthology: true
  season: 1
  episodes: [5, 6]
  status: auto
  show_name: "Paw Patrol"
  expected_confidence: 0.85
```

### Manual Review Required
```yaml
- file: "Harvey Girls Forever/Harvey Girls Forever! - S01E01 - War and Trees WEBDL-1080p.mkv"
  anthology: true
  title_trusted: false
  season: 1
  episodes: [1, 2]
  status: manual
  reason: "Untrusted episode titles require manual verification"
```

### Unsupported File
```yaml
- file: "Unsupported/malformed-filename-no-pattern.mp4"
  status: unsupported
  reason: "No recognizable episode pattern"
```

## Shows Covered

The manifest includes test files for the following TV shows:

1. **Paw Patrol** (anthology format)
2. **Harvey Girls Forever** (anthology format)
3. **Martha Speaks** (standard format)
4. **The Octonauts** (standard format)
5. **Firebuds** (anthology format)

## Statistics

- **Total entries**: 4,950+ 
- **Auto-processed**: ~80% of entries
- **Manual review**: ~15% of entries
- **Unsupported**: ~5% of entries (23 specific test files)

## Validation Rules

The manifest is validated by the regression test suite:

1. **File existence**: All referenced files must exist in the test directory
2. **Field consistency**: Required fields must be present and valid
3. **Episode logic**: Episode numbers must be consistent with anthology flag
4. **Status alignment**: Expected status must match actual processing outcome

## Usage in Tests

The manifest is loaded by the regression test suite in `tests/integration/test_tv_scan_regression.py`:

```python
# Load the fixture manifest to understand the test data
manifest_path = self.fixture_root / "fixture_manifest.yaml"
if manifest_path.exists():
    with open(manifest_path) as f:
        self.manifest = yaml.safe_load(f)
```

The manifest data is used to:
- Validate scan results against expected outcomes
- Filter test files by status or criteria
- Provide context for test failures and debugging
- Generate test reports and coverage metrics

## Adding New Entries

To add new entries to the manifest:

1. **Add test files** to the appropriate directory under `tests/mocks/tv/`
2. **Create manifest entries** following the format above
3. **Run tests** to validate the new entries
4. **Update documentation** if new fields or patterns are added

## Maintenance

The manifest should be updated whenever:
- New test files are added to the regression suite
- Test file behavior changes (e.g., confidence thresholds)
- New fields are needed for test validation
- Shows or episodes are added/removed from the test suite

The manifest serves as the single source of truth for test expectations and should be kept synchronized with the actual test files and expected behaviors. 
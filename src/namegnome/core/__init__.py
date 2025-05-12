"""Core functionality for namegnome.

This package exposes the main scanning and media type guessing functions for use
by CLI and other modules.
- scan_directory: Recursively scans directories for media files, classifies, and
  returns results.
- guess_media_type: Heuristically determines the type of a media file based on
  path, extension, and naming patterns.

See scanner.py for implementation details and reasoning behind classification
logic.
"""

from namegnome.core.scanner import guess_media_type, scan_directory

# Reason: Only expose the main scanning and classification API to consumers of
# the core package.
__all__ = ["guess_media_type", "scan_directory"]

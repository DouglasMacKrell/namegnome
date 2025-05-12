"""JSON serialization helpers for namegnome.

This module provides helpers for serializing objects to JSON, especially for
types not natively supported by the standard library (e.g., datetime,
pathlib.Path).
- Used throughout namegnome for robust, cross-platform serialization of plans,
  metadata, and logs.
- Ensures that datetime objects are stored in ISO 8601 format for portability
  and auditability.
- Ensures Path objects are serialized as strings for compatibility across OSes
  and filesystems.

Design:
- Custom encoder handles datetime and Path objects.
- Extendable for additional types as needed.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Self


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for namegnome.

    Handles serialization of datetime and Path objects, which are common in plan
    metadata and logs. Extend this class to add support for additional types as
    needed.
    """

    def default(self: Self, obj: object) -> Any:  # noqa: ANN401
        """Convert objects to JSON-serializable format.

        Args:
            obj: Object to serialize (may be datetime, Path, or other types)

        Returns:
            JSON-serializable representation of the object.
            - datetime: ISO 8601 string (portable, human-readable)
            - Path: string (cross-platform compatibility)
            - Otherwise: falls back to base class
        """
        # Reason: datetime is not JSON serializable by default; ISO 8601 is
        # standard for logs/metadata.
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Reason: Path objects are used throughout namegnome for file operations;
        # serialize as string for portability.
        if isinstance(obj, Path):
            return str(obj)
        # Let the base class default method handle it or raise TypeError
        return super().default(obj)

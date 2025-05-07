"""JSON utilities for namegnome."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and Path objects."""

    def default(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation of the object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

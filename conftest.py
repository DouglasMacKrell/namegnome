"""Configure pytest."""

import os
import sys
from pathlib import Path

# Get the project root directory
root_dir = Path(__file__).parent

# Add src directory to Python path
src_path = str(root_dir / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Remove any duplicate paths
sys.path = list(dict.fromkeys(sys.path))

# Set PYTHONPATH environment variable
os.environ["PYTHONPATH"] = src_path

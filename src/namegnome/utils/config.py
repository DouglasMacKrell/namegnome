"""Config utility for persistent NameGnome settings (LLM model, etc.).

Provides functions to read and write the default LLM model to
~/.config/namegnome/config.toml. Uses tomli/tomli-w for TOML parsing and writing.
"""

from pathlib import Path
from typing import Optional

import tomli
import tomli_w

CONFIG_DIR = Path.home() / ".config" / "namegnome"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def get_default_llm_model() -> Optional[str]:
    """Read the default LLM model from config.toml.

    Returns:
        Optional[str]: The default LLM model name, or 'llama3:8b' if not set.
    """
    if not CONFIG_FILE.exists():
        return "llama3:8b"
    with CONFIG_FILE.open("rb") as f:
        data = tomli.load(f)
    return data.get("llm", {}).get("default_model") or "llama3:8b"


def set_default_llm_model(model: str) -> None:
    """Set the default LLM model in config.toml.

    Args:
        model (str): The model name to set as default.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("rb") as f:
            data = tomli.load(f)
    if "llm" not in data:
        data["llm"] = {}
    data["llm"]["default_model"] = model
    with CONFIG_FILE.open("wb") as f:
        tomli_w.dump(data, f)

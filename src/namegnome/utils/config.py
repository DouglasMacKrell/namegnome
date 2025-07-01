"""Config utility for persistent NameGnome settings (LLM model, etc.).

Provides functions to read and write the default LLM model to
~/.config/namegnome/config.toml. Uses tomli/tomli-w for TOML parsing and writing.
"""

from pathlib import Path
from typing import Optional, TypeVar, Any, cast
import os
import contextlib

import tomli
import tomli_w

# Determine config directory respecting XDG_CONFIG_HOME if set.
_xdg_config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
# Path like ~/.config/namegnome or $XDG_CONFIG_HOME/namegnome
CONFIG_DIR = _xdg_config_home / "namegnome"
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


# ---------------------------------------------------------------------------
# Generic configuration resolution
# ---------------------------------------------------------------------------

T = TypeVar("T")


def _read_config_file() -> dict[str, Any]:
    """Read the TOML config file if it exists, returning a (nested) dict."""

    if not CONFIG_FILE.exists():
        return {}
    with CONFIG_FILE.open("rb") as f:
        return tomli.load(f)


def _lookup_nested(data: dict[str, Any], dotted_key: str) -> Any | None:
    """Retrieve a nested value from *data* given a dotted key path.

    Example: dotted_key="llm.default_model" will attempt
    ``data["llm"]["default_model"]`` returning None if any level is missing.
    """

    keys = dotted_key.split(".")
    current: Any = data
    for part in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current


def _make_env_var_name(dotted_key: str, prefix: str = "NAMEGNOME_") -> str:
    """Convert a dotted key path to an uppercase ENV var name.

    Example: "llm.default_model" -> "NAMEGNOME_LLM_DEFAULT_MODEL".
    """

    return prefix + dotted_key.replace(".", "_").upper()


def resolve_setting(
    key: str,
    *,
    default: T,
    cli_value: T | None = None,
) -> T:
    """Resolve a configuration *key* using precedence CLI > env > config > default.

    Args:
        key: Dotted key path, e.g. ``"llm.default_model"`` or ``"foo"``.
        default: Value to fall back to when no overrides found.
        cli_value: Value passed from CLI option (may be ``None`` when not provided).

    Returns:
        The resolved value with type matching *default* (or *cli_value*).
    """

    # 1. CLI value wins if provided (and not ``None`` to mimic Typer semantics).
    if cli_value is not None:
        return cli_value

    # 2. Environment variable
    env_var = _make_env_var_name(key)
    if env_var in os.environ:
        env_val: str = os.environ[env_var]
        # Attempt best-effort type coercion based on *default* value
        if isinstance(default, bool):
            return cast(T, env_val.lower() in {"1", "true", "yes", "on"})
        if isinstance(default, int):
            try:
                return cast(T, int(env_val))
            except ValueError:
                return default
        if isinstance(default, float):
            with contextlib.suppress(ValueError):
                return cast(T, float(env_val))
        # If default is None (type unknown) try to infer int/float automatically.
        if default is None:
            if env_val.isdigit():
                return cast(T, int(env_val))
            with contextlib.suppress(ValueError):
                return cast(T, float(env_val))
        # Fallback: return as string type
        return cast(T, env_val)

    # 3. Config file lookup
    cfg_data = _read_config_file()
    file_val = _lookup_nested(cfg_data, key)
    if file_val is not None:
        # Validate / coerce to match default's type when possible
        if isinstance(default, bool):
            if isinstance(file_val, bool):
                return cast(T, file_val)
            # Attempt to parse truthy strings
            if isinstance(file_val, str):
                return cast(T, file_val.lower() in {"1", "true", "yes", "on"})
            return default
        if isinstance(default, int):
            if isinstance(file_val, int):
                return cast(T, file_val)
            if isinstance(file_val, str):
                with contextlib.suppress(ValueError):
                    return cast(T, int(file_val))
            return default
        if isinstance(default, float):
            if isinstance(file_val, (int, float)):
                return cast(T, float(file_val))
            if isinstance(file_val, str):
                with contextlib.suppress(ValueError):
                    return cast(T, float(file_val))
            return default
        if default is None:
            # Attempt to coerce basic scalar types for None default
            if isinstance(file_val, bool):
                return cast(T, file_val)
            if isinstance(file_val, int):
                return cast(T, file_val)
            if isinstance(file_val, str):
                if file_val.isdigit():
                    return cast(T, int(file_val))
                with contextlib.suppress(ValueError):
                    return cast(T, float(file_val))
            # otherwise return as-is
            return cast(T, file_val)

        # For non-scalar defaults (e.g., str) just return the config value
        return cast(T, file_val)

    # 4. Default
    return default

import importlib
import pytest

from namegnome.utils import config as cfg


@pytest.fixture()
def reload_config(tmp_path, monkeypatch):
    """Reload utils.config after patching HOME/XDG directories.

    Ensures CONFIG_DIR/FILE constants are recalculated for a temporary home dir
    so tests do not interfere with the real user config.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    # Reload module so that Path.home() & env vars are re-evaluated
    importlib.reload(cfg)
    return fake_home


def test_resolve_setting_cli_over_env_over_config(reload_config, monkeypatch, tmp_path):
    # Prepare env var and config, then ensure cli_value wins
    monkeypatch.setenv("NAMEGNOME_FOO", "from-env")

    # Write config value
    cfg.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg.CONFIG_FILE.write_text('foo = "from-config"\n')

    # When cli_value provided, it should be returned regardless
    result = cfg.resolve_setting("foo", default="default", cli_value="from-cli")
    assert result == "from-cli"


def test_resolve_setting_env_over_config(reload_config, monkeypatch, tmp_path):
    # Env var should override config file when cli_value is None
    monkeypatch.setenv("NAMEGNOME_BAR", "from-env")
    cfg.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg.CONFIG_FILE.write_text('bar = "from-config"\n')

    result = cfg.resolve_setting("bar", default="default")
    assert result == "from-env"


def test_resolve_setting_config_when_no_env(reload_config, monkeypatch, tmp_path):
    # Should return config file value when env var missing
    cfg.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg.CONFIG_FILE.write_text('baz = "from-config"\n')

    result = cfg.resolve_setting("baz", default="default")
    assert result == "from-config"


def test_resolve_setting_default_when_missing(reload_config):
    # Should fall back to default when no other sources
    result = cfg.resolve_setting("missing", default="default-value")
    assert result == "default-value"


def test_resolve_llm_model_env_over_default(reload_config, monkeypatch):
    """Env var should override default for llm.default_model."""
    monkeypatch.setenv("NAMEGNOME_LLM_DEFAULT_MODEL", "gpt-4o")
    result = cfg.resolve_setting("llm.default_model", default="llama3:8b")
    assert result == "gpt-4o"


def test_resolve_llm_model_config_when_no_env(reload_config):
    """Config file value should be used when env var is absent."""
    cfg.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg.CONFIG_FILE.write_text('[llm]\ndefault_model = "codellama"\n')

    result = cfg.resolve_setting("llm.default_model", default="llama3:8b")
    assert result == "codellama"


def test_resolve_verify_env(reload_config, monkeypatch):
    monkeypatch.setenv("NAMEGNOME_SCAN_VERIFY_HASH", "1")
    result = cfg.resolve_setting("scan.verify_hash", default=False)
    assert result is True


def test_resolve_strict_directory_structure_config(reload_config):
    cfg.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg.CONFIG_FILE.write_text("[scan]\nstrict_directory_structure = false\n")
    result = cfg.resolve_setting("scan.strict_directory_structure", default=True)
    assert result is False


def test_resolve_max_duration_env(reload_config, monkeypatch):
    monkeypatch.setenv("NAMEGNOME_TV_MAX_DURATION", "60")
    result = cfg.resolve_setting("tv.max_duration", default=None)
    assert result == 60


def test_resolve_invalid_int_env_falls_back(reload_config, monkeypatch):
    monkeypatch.setenv("NAMEGNOME_TV_MAX_DURATION", "notanint")
    result = cfg.resolve_setting("tv.max_duration", default=30)
    # Should fall back to default because conversion fails
    assert result == 30


def test_resolve_invalid_int_config_falls_back(reload_config):
    cfg.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg.CONFIG_FILE.write_text('[tv]\nmax_duration = "notanint"\n')
    result = cfg.resolve_setting("tv.max_duration", default=45)
    assert result == 45

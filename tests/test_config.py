"""Unit tests for guardian.core.config module."""

import os
import pytest
from guardian.core.config import GuardianConfig, load_config
from guardian.core.exceptions import ConfigError


def test_default_config():
    """Verify default configuration initialization."""
    config = GuardianConfig()
    assert config.app_name == "GuardianAI"
    assert config.version == "0.1.0"
    assert config.environment == "development"
    assert config.log_level == "INFO"
    assert config.dev_mode is True


def test_env_override(monkeypatch):
    """Verify environment variables override defaults."""
    monkeypatch.setenv("GUARDIAN_APP_NAME", "TestGuardian")
    monkeypatch.setenv("GUARDIAN_ENV", "production")
    monkeypatch.setenv("GUARDIAN_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("GUARDIAN_DEV_MODE", "false")

    config = load_config()
    assert config.app_name == "TestGuardian"
    assert config.environment == "production"
    assert config.log_level == "DEBUG"
    assert config.dev_mode is False


def test_invalid_log_level(monkeypatch):
    """Verify exception raised on invalid log level."""
    monkeypatch.setenv("GUARDIAN_LOG_LEVEL", "INVALID_LEVEL")
    with pytest.raises(ConfigError) as exc_info:
        load_config()
    assert "Invalid log_level" in str(exc_info.value)


def test_missing_config_file():
    """Verify exception raised when non-existent config file specified."""
    with pytest.raises(ConfigError) as exc_info:
        load_config(config_path="non_existent_file.yaml")
    assert "not found" in str(exc_info.value)

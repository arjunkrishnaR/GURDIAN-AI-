"""Centralized configuration management for GuardianAI."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yaml
    HAS_YAML = True
except ImportError:  # pragma: no cover
    HAS_YAML = False

from guardian.core.exceptions import ConfigError


@dataclass
class GuardianConfig:
    """GuardianAI configuration data structure."""
    app_name: str = "GuardianAI"
    version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "guardian.log"
    data_dir: str = "data"
    dev_mode: bool = True
    debug_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "environment": self.environment,
            "log_level": self.log_level,
            "log_dir": self.log_dir,
            "log_file": self.log_file,
            "data_dir": self.data_dir,
            "dev_mode": self.dev_mode,
            "debug_mode": self.debug_mode,
        }


def load_config(config_path: Optional[str] = None) -> GuardianConfig:
    """
    Load configuration deterministically from defaults, optional YAML file, and environment variables.
    
    Priority:
    1. Environment variables (GUARDIAN_*)
    2. YAML config file (if specified or default existing file)
    3. Defaults defined in GuardianConfig dataclass
    """
    data: Dict[str, Any] = {}

    # 1. Load from YAML file if provided or default config exists
    target_yaml: Optional[Path] = None
    if config_path:
        target_yaml = Path(config_path)
        if not target_yaml.exists():
            raise ConfigError(f"Specified configuration file not found: {config_path}")
    else:
        default_yaml = Path("config/config.example.yaml")
        if default_yaml.exists():
            target_yaml = default_yaml

    if target_yaml and target_yaml.exists():
        if not HAS_YAML:  # pragma: no cover
            raise ConfigError("PyYAML dependency missing, cannot parse YAML configuration.")
        try:
            with open(target_yaml, "r", encoding="utf-8") as f:
                parsed = yaml.safe_load(f) or {}
                if not isinstance(parsed, dict):
                    raise ConfigError(f"Configuration file root must be a YAML dictionary: {target_yaml}")

                app_cfg = parsed.get("app", {})
                log_cfg = parsed.get("logging", {})
                storage_cfg = parsed.get("storage", {})

                if "name" in app_cfg:
                    data["app_name"] = str(app_cfg["name"])
                if "version" in app_cfg:
                    data["version"] = str(app_cfg["version"])
                if "environment" in app_cfg:
                    data["environment"] = str(app_cfg["environment"])
                if "dev_mode" in app_cfg:
                    data["dev_mode"] = bool(app_cfg["dev_mode"])
                if "debug_mode" in app_cfg:
                    data["debug_mode"] = bool(app_cfg["debug_mode"])

                if "log_level" in log_cfg:
                    data["log_level"] = str(log_cfg["log_level"]).upper()
                if "log_dir" in log_cfg:
                    data["log_dir"] = str(log_cfg["log_dir"])
                if "log_file" in log_cfg:
                    data["log_file"] = str(log_cfg["log_file"])

                if "data_dir" in storage_cfg:
                    data["data_dir"] = str(storage_cfg["data_dir"])

        except Exception as e:
            if isinstance(e, ConfigError):
                raise
            raise ConfigError(f"Error parsing YAML config file {target_yaml}: {e}") from e

    # 2. Apply Environment Variables Overrides (GUARDIAN_*)
    env_mapping = {
        "GUARDIAN_APP_NAME": "app_name",
        "GUARDIAN_ENV": "environment",
        "GUARDIAN_LOG_LEVEL": "log_level",
        "GUARDIAN_LOG_DIR": "log_dir",
        "GUARDIAN_DATA_DIR": "data_dir",
    }
    for env_var, cfg_key in env_mapping.items():
        if env_var in os.environ:
            data[cfg_key] = os.environ[env_var]

    if "GUARDIAN_DEV_MODE" in os.environ:
        data["dev_mode"] = os.environ["GUARDIAN_DEV_MODE"].lower() in ("true", "1", "yes")
    if "GUARDIAN_DEBUG_MODE" in os.environ:
        data["debug_mode"] = os.environ["GUARDIAN_DEBUG_MODE"].lower() in ("true", "1", "yes")

    config = GuardianConfig(**data)
    _validate_config(config)
    return config


def _validate_config(config: GuardianConfig) -> None:
    """Validate configuration parameters."""
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if config.log_level.upper() not in valid_levels:
        raise ConfigError(f"Invalid log_level '{config.log_level}'. Must be one of {valid_levels}")

    if not config.app_name.strip():
        raise ConfigError("app_name configuration cannot be empty.")

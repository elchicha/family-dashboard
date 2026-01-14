from pathlib import Path
from typing import Optional

import yaml


class ConfigService:
    def __init__(self, config_file: str = ""):
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        with open(self.config_file, "r") as f:
            configs = yaml.safe_load(f)
        return configs

    def get(self, param, default: Optional = ""):
        """Get config value using dot notation"""
        keys = param.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

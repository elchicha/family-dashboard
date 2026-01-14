import pytest
import tempfile
from pathlib import Path
import yaml
from src.services.config_service import ConfigService


class TestConfigService:

    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file for testing"""
        config_data = {
            "display": {"width": 800, "height": 400, "type": "png"},
            "weather": {
                "enabled": True,
                "city": "London",
                "units": "celsius",
                "api_key": "test_api_key_12345",
            },
            "calendar": {
                "enabled": True,
                "source": "local_file",
                "local_file": {"path": "./data/calendar.json"},
            },
            "shopping_list": {
                "file": "./data/shopping_list.json",
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        yield temp_path

        Path(temp_path).unlink()

    def test_config_service_loads_yaml_file(self, temp_config_file):
        """Service should load configuration from YAML"""
        config = ConfigService(config_file=temp_config_file)

        assert config.get("weather.city") == "London"
        assert config.get("weather.units") == "celsius"
        assert config.get("display.width") == 800

    def test_config_service_get_with_default(self, temp_config_file):
        """Should return default value if key doesn't exist"""
        config = ConfigService(config_file=temp_config_file)

        value = config.get("nonexistent.key", default="fallback")
        assert value == "fallback"

    def test_config_service_get_nested_values(self, temp_config_file):
        """Should access nested config with dot notation"""
        config = ConfigService(config_file=temp_config_file)

        assert config.get("weather.api_key") == "test_api_key_12345"
        assert config.get("shopping_list.file") == "./data/shopping_list.json"

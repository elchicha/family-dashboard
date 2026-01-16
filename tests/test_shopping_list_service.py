import pytest
import json
import tempfile
from pathlib import Path
from src.services.shopping_list_service import ShoppingListService


class TestShoppingListService:

    @pytest.fixture
    def temp_shopping_file(self):
        """Create temporary shopping list JSON file"""
        data = {
            "items": [
                {"name": "Milk", "checked": False, "category": "Dairy"},
                {"name": "Bread", "checked": False, "category": "Bakery"},
                {"name": "Eggs", "checked": True, "category": "Dairy"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(data, f)
            temp_path = f.name

        yield temp_path

        Path(temp_path).unlink()

    def test_shopping_list_service_loads_items(self, temp_shopping_file):
        """Service should load items from JSON file"""
        service = ShoppingListService(data_file=temp_shopping_file)
        items = service.get_items()

        assert len(items) == 3
        assert items[0]["name"] == "Milk"
        assert items[0]["checked"] == False

    def test_shopping_list_service_filters_unchecked(self, temp_shopping_file):
        """Service should return only unchecked items"""
        service = ShoppingListService(data_file=temp_shopping_file)
        unchecked = service.get_unchecked_items()

        assert len(unchecked) == 2
        assert all(not item["checked"] for item in unchecked)
        assert "Eggs" not in [item["name"] for item in unchecked]

    def test_shopping_list_service_creates_file_if_missing(self):
        """Service should create data file if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "shopping_list.json"

            service = ShoppingListService(data_file=str(data_file))

            # File should be created
            assert data_file.exists()

            # Should contain empty list
            items = service.get_items()
            assert items == []

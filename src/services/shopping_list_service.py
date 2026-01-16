import json
from pathlib import Path


class ShoppingListService:
    def __init__(self, data_file: str = "./data/shopping_list.json"):
        self.data_file = Path(data_file)

    def _load_data(self) -> dict:
        """Load data from JSON file"""
        with open(self.data_file, "r") as f:
            return json.load(f)

    def get_items(self):
        item_list = self._load_data()
        return item_list.get("items", "")

import json
from pathlib import Path


class ShoppingListService:
    def __init__(self, data_file: str = "./data/shopping_list.json"):
        self.data_file = self._initialize_data_file(data_file)

    def _load_data(self) -> list:
        """Load data from JSON file"""
        with open(self.data_file, "r") as f:
            data = json.load(f)
        return data.get("items", [])

    def _initialize_data_file(self, data_file: str):
        data_file_path = Path(data_file)
        if not data_file_path.exists():
            empty_item_list = {"items": []}
            data_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(data_file_path, "w") as f:
                json.dump(empty_item_list, f)
        return data_file_path

    def get_items(self) -> list:
        return self._load_data()

    def get_unchecked_items(self) -> list:
        return [item for item in self.get_items() if not item["checked"]]

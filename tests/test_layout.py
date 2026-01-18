import pytest
from src.layout.layout_interface import LayoutInterface
from src.layout.three_column_layout import ThreeColumnLayout


@pytest.fixture
def layout():
    """Fixture that creates a Layout instance"""
    return ThreeColumnLayout()


class TestThreeColumnLayout:
    def test_layout_implements_interface(self, layout):
        assert isinstance(layout, LayoutInterface)

    def test_layout_has_three_columns(self, layout):
        """Layout should divide the screen into 3 columns"""
        assert len(layout.columns) == 3

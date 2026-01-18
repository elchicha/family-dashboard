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

    def test_layout_calculates_column_widths(self):
        """Each column should have equal width based on screen size"""
        layout = ThreeColumnLayout(width=1872, height=1404)

        assert layout.column_width == 624

    def test_add_widget_to_column(self, layout):
        """Should be able to add widgets to specific columns"""
        from src.widgets.clock_widget import ClockWidget

        widget = ClockWidget()
        layout.add_widget(widget, column=0)

        assert len(layout.columns[0]) == 1
        assert layout.columns[0][0] == widget

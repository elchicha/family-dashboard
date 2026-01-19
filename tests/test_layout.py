import pytest
from src.layout.layout_interface import LayoutInterface
from src.layout.three_column_layout import ThreeColumnLayout


# At the top of your test file, add a mock widget class
class MockWidget:
    def __init__(self, height=100):
        self.height = height
        self.rendered_at = None  # Track where it was rendered

    def render(self, display, x_offset=0, y_offset=0):
        self.rendered_at = (x_offset, y_offset)


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

    def test_render_positions_widgets_correctly(self, layout):
        """Layout should position widgets in correct columns with correct offsets"""
        layout = ThreeColumnLayout(width=1872, height=1404)

        widget1 = MockWidget(height=100)
        widget2 = MockWidget(height=150)
        widget3 = MockWidget(height=200)

        layout.add_widget(widget1, column=0)
        layout.add_widget(widget2, column=1)
        layout.add_widget(widget3, column=0)  # Second widget in column 0

        # Mock display
        display = None  # We'll pass None since MockWidget doesn't use it

        layout.render(display)

        # Check positions
        assert widget1.rendered_at == (0, 0)  # Column 0, top
        assert widget2.rendered_at == (624, 0)  # Column 1, top
        assert widget3.rendered_at == (0, 100)  # Column 0, below widget1

    @pytest.mark.parametrize(
        "width,height,expected_col_width",
        [
            (800, 480, 266),  # 7.5" E-Ink display (ESP32)
            (960, 680, 320),  # 13.3" E-Ink HAT (Pi)
            (1872, 1404, 624),  # 10.3" (legacy support)
        ],
    )
    def test_layout_supports_multiple_resolutions(
        self, width, height, expected_col_width
    ):
        """Layout should correctly calculate column widths for different display sizes"""
        layout = ThreeColumnLayout(width=width, height=height)
        assert layout.column_width == expected_col_width
        assert layout.width == width
        assert layout.height == height

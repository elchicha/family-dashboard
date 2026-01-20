import pytest
from src.layout.layout_interface import LayoutInterface
from src.layout.three_column_layout import ThreeColumnLayout
from src.layout.two_column_layout import TwoColumnLayout


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


@pytest.fixture
def two_column_layout():
    """Fixture that creates a TwoColumnLayout instance"""
    return TwoColumnLayout()


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


class TestTwoColumnLayout:
    """Test suite for TwoColumnLayout with asymmetric columns."""

    def test_layout_implements_interface(self, two_column_layout):
        """Should implement LayoutInterface."""
        assert isinstance(two_column_layout, LayoutInterface)

    def test_default_layout_is_800x480(self):
        """Should default to 7.5\" E-Ink dimensions."""
        layout = TwoColumnLayout()
        assert layout.width == 800
        assert layout.height == 480

    def test_supports_custom_dimensions(self):
        """Should support custom display sizes."""
        layout = TwoColumnLayout(width=1872, height=1404)
        assert layout.width == 1872
        assert layout.height == 1404

    def test_default_split_is_60_40(self):
        """Should use 60/40 asymmetric split by default."""
        layout = TwoColumnLayout()
        # 60% of 800 = 480px
        assert layout.left_width == 480
        # 40% of 800 = 320px
        assert layout.right_width == 320

    @pytest.mark.parametrize(
        "left_ratio,expected_left,expected_right",
        [
            (0.5, 400, 400),  # 50/50 balanced
            (0.6, 480, 320),  # 60/40 default
            (0.7, 560, 240),  # 70/30 wide main
            (0.4, 320, 480),  # 40/60 sidebar first
            (0.3, 240, 560),  # 30/70 narrow sidebar
        ],
    )
    def test_supports_custom_split_ratios(
        self, left_ratio, expected_left, expected_right
    ):
        """Should support various column width ratios."""
        layout = TwoColumnLayout(left_ratio=left_ratio)
        assert layout.left_width == expected_left
        assert layout.right_width == expected_right

    def test_has_two_columns(self, two_column_layout):
        """Should have exactly two columns."""
        assert hasattr(two_column_layout, "left_column")
        assert hasattr(two_column_layout, "right_column")
        assert isinstance(two_column_layout.left_column, list)
        assert isinstance(two_column_layout.right_column, list)

    def test_add_widget_to_left_column(self, two_column_layout):
        """Should add widgets to left column."""
        widget = MockWidget()

        two_column_layout.add_widget(widget, column="left")

        assert widget in two_column_layout.left_column
        assert len(two_column_layout.left_column) == 1

    def test_add_widget_to_right_column(self, two_column_layout):
        """Should add widgets to right column."""
        widget = MockWidget()

        two_column_layout.add_widget(widget, column="right")

        assert widget in two_column_layout.right_column
        assert len(two_column_layout.right_column) == 1

    def test_add_multiple_widgets_to_same_column(self, two_column_layout):
        """Should stack multiple widgets vertically."""
        widget1 = MockWidget(height=100)
        widget2 = MockWidget(height=150)

        two_column_layout.add_widget(widget1, column="left")
        two_column_layout.add_widget(widget2, column="left")

        assert len(two_column_layout.left_column) == 2
        assert two_column_layout.left_column[0] == widget1
        assert two_column_layout.left_column[1] == widget2

    def test_rejects_invalid_column_name(self, two_column_layout):
        """Should raise error for invalid column."""
        widget = MockWidget()

        with pytest.raises(ValueError, match="Column must be 'left' or 'right'"):
            two_column_layout.add_widget(widget, column="middle")

    def test_render_positions_left_column_at_zero(self, two_column_layout):
        """Left column should start at x=0."""
        widget = MockWidget(height=100)
        two_column_layout.add_widget(widget, column="left")

        two_column_layout.render(display=None)

        assert widget.rendered_at == (0, 0)

    def test_render_positions_right_column_after_left(self):
        """Right column should start after left column width."""
        layout = TwoColumnLayout()  # Default 60/40 = 480/320
        widget = MockWidget(height=100)
        layout.add_widget(widget, column="right")

        layout.render(display=None)

        # Right column starts at left_width (480px by default)
        assert widget.rendered_at == (480, 0)

    def test_render_stacks_widgets_vertically(self, two_column_layout):
        """Should stack widgets vertically based on height."""
        widget1 = MockWidget(height=100)
        widget2 = MockWidget(height=150)
        widget3 = MockWidget(height=200)

        two_column_layout.add_widget(widget1, column="left")
        two_column_layout.add_widget(widget2, column="left")
        two_column_layout.add_widget(widget3, column="left")

        two_column_layout.render(display=None)

        # First widget at top
        assert widget1.rendered_at == (0, 0)
        # Second widget below first
        assert widget2.rendered_at == (0, 100)
        # Third widget below second
        assert widget3.rendered_at == (0, 250)  # 100 + 150

    def test_render_with_widget_spacing(self):
        """Should support spacing between widgets."""
        layout = TwoColumnLayout(widget_spacing=20)
        widget1 = MockWidget(height=100)
        widget2 = MockWidget(height=150)

        layout.add_widget(widget1, column="left")
        layout.add_widget(widget2, column="left")

        layout.render(display=None)

        # Second widget should have gap
        assert widget1.rendered_at == (0, 0)
        assert widget2.rendered_at == (0, 120)  # 100 + 20 spacing

    def test_columns_render_independently(self):
        """Widgets in different columns should not affect each other's y-position."""
        layout = TwoColumnLayout()
        left_widget = MockWidget(height=300)
        right_widget = MockWidget(height=100)

        layout.add_widget(left_widget, column="left")
        layout.add_widget(right_widget, column="right")

        layout.render(display=None)

        # Both start at y=0 (independent stacking)
        assert left_widget.rendered_at == (0, 0)
        assert right_widget.rendered_at == (480, 0)

    def test_spacing_applies_to_both_columns(self):
        """Widget spacing should apply to both columns independently."""
        layout = TwoColumnLayout(widget_spacing=15)

        left1 = MockWidget(height=100)
        left2 = MockWidget(height=100)
        right1 = MockWidget(height=150)
        right2 = MockWidget(height=150)

        layout.add_widget(left1, column="left")
        layout.add_widget(left2, column="left")
        layout.add_widget(right1, column="right")
        layout.add_widget(right2, column="right")

        layout.render(display=None)

        # Left column stacking
        assert left1.rendered_at == (0, 0)
        assert left2.rendered_at == (0, 115)  # 100 + 15

        # Right column stacking
        assert right1.rendered_at == (480, 0)
        assert right2.rendered_at == (480, 165)  # 150 + 15

    @pytest.mark.parametrize(
        "width,left_ratio,expected_left,expected_right",
        [
            (800, 0.6, 480, 320),  # 7.5" E-Ink default
            (960, 0.5, 480, 480),  # 13.3" balanced
            (1872, 0.7, 1310, 562),  # 10.3" wide main
        ],
    )
    def test_layout_supports_multiple_resolutions(
        self, width, left_ratio, expected_left, expected_right
    ):
        """Layout should correctly calculate column widths for different display sizes."""
        layout = TwoColumnLayout(width=width, height=480, left_ratio=left_ratio)
        assert layout.left_width == expected_left
        assert layout.right_width == expected_right
        assert layout.left_width + layout.right_width == width

    def test_rejects_invalid_ratio(self):
        """Should reject ratios outside 0-1 range."""
        with pytest.raises(ValueError, match="left_ratio must be between 0 and 1"):
            TwoColumnLayout(left_ratio=1.5)

        with pytest.raises(ValueError, match="left_ratio must be between 0 and 1"):
            TwoColumnLayout(left_ratio=-0.1)

        with pytest.raises(ValueError, match="left_ratio must be between 0 and 1"):
            TwoColumnLayout(left_ratio=0)  # Can't have 0-width column

        with pytest.raises(ValueError, match="left_ratio must be between 0 and 1"):
            TwoColumnLayout(left_ratio=1)  # Can't have 0-width column

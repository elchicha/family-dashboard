from src.display.display_interface import DisplayRenderer


class TestDisplayRenderer:
    """Test the DisplayRenderer class."""

    def test_renderer_creates_image_with_correct_dimensions(self):
        """Test that renderer creates an image with the specified dimensions."""
        width, height = 800, 480
        renderer = DisplayRenderer(width=width, height=height)

        image = renderer.create_blank_canvas()

        assert image.size == (width, height)
        assert image.mode == "RGB"
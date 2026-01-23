from PIL import Image, ImageDraw, ImageFont
from src.display.display_interface import DisplayInterface
import os


class PNGDisplay(DisplayInterface):
    """Renders display output to a PNG file"""

    def __init__(self, width: int, height: int, output_path: str = None):
        super().__init__(width, height)
        self.output_path = output_path
        self.image = Image.new("RGB", (width, height), "white")
        self.draw = ImageDraw.Draw(self.image)
        self._font_cache = {}  # Cache loaded fonts

    def clear(self):
        """Clear to white background"""
        self.draw.rectangle([(0, 0), (self.width, self.height)], fill="white")

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: str = "#000000", width: int = 1):
        """Draw a line on the display."""
        self.draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    def _get_font(self, font_size: int):
        """
        Get a font at the specified size, with caching.

        Tries multiple font paths for cross-platform compatibility.
        Falls back to default font if no TrueType fonts found.
        """
        # Check cache first
        if font_size in self._font_cache:
            return self._font_cache[font_size]

        # Try to find a TrueType font
        font_paths = [
            # Linux paths
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
            # macOS paths
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSText.ttf",
            "/Library/Fonts/Arial.ttf",
            # Windows paths
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\calibri.ttf",
        ]

        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    print(f"✅ Loaded font: {font_path} at size {font_size}")
                    break
                except Exception as e:
                    continue

        # If no TrueType font found, fall back to default
        if font is None:
            print(f"⚠️  No TrueType fonts found - using default font (size control limited)")
            font = ImageFont.load_default()

        # Cache the font
        self._font_cache[font_size] = font
        return font

    def draw_text(
            self, x_pos: int, y_pos: int, text: str, font_size: int, color: str = "#000000"
    ):
        """Draw text on the image"""
        font = self._get_font(font_size)
        self.draw.text((x_pos, y_pos), str(text), fill=color, font=font)

    def draw_rectangle(
            self,
            x_pos: int,
            y_pos: int,
            width: int,
            height: int,
            fill: str | None = None,
            outline: str = "#000000",
    ):
        """Draw a rectangle with optional fill and outline"""
        coords = [(x_pos, y_pos), (x_pos + width, y_pos + height)]
        self.draw.rectangle(coords, fill=fill, outline=outline)

    def refresh(self):
        """Save the image to file"""
        self.image.save(self.output_path)
        print(f"Dashboard saved to {self.output_path}")

    def get_image_bytes(self) -> bytes:
        """
        Get PNG image as bytes.

        Returns:
            PNG image data as bytes
        """
        from io import BytesIO

        buffer = BytesIO()
        self.image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.read()
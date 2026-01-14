from PIL import Image, ImageDraw, ImageFont
from src.display.display_interface import DisplayInterface


class PNGDisplay(DisplayInterface):
    """Renders display output to a PNG file"""

    def __init__(self, width: int, height: int, output_path: str):
        super().__init__(width, height)
        self.output_path = output_path
        self.image = Image.new("RGB", (width, height), "white")
        self.draw = ImageDraw.Draw(self.image)

    def clear(self):
        """Clear to white background"""
        self.draw.rectangle([(0, 0), (self.width, self.height)], fill="white")

    def draw_line(
        self, x1: int, y1: int, x2: int, y2: int, color: str = "black", width: int = 1
    ):
        """Draw a line on the image"""
        self.draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    def draw_text(self, x_pos: int, y_pos: int, text: str, font_size: int):
        """Draw text on the image"""
        try:
            # Try to use a nice font
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
            )
        except:
            # Fall back to default
            font = ImageFont.load_default()

        self.draw.text((x_pos, y_pos), str(text), fill="black", font=font)

    def refresh(self):
        """Save the image to file"""
        self.image.save(self.output_path)
        print(f"Dashboard saved to {self.output_path}")

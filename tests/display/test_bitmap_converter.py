import pytest
from PIL import Image


class TestBitmapConverter:
    """Test the bitmap converter for e-ink displays"""

    def test_import_bitmap_converter(self):
        """Should be able to import the bitmap converter module"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap
        assert callable(pil_to_1bit_bitmap)

    def test_output_size_800x480(self):
        """Converter should produce exactly 48000 bytes for 800x480 display"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap

        image = Image.new("RGB", (800, 480), "white")
        bitmap = pil_to_1bit_bitmap(image)
        assert len(bitmap) == 48000  # 800 * 480 / 8

    def test_output_is_bytes(self):
        """Converter should return bytes object"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap

        image = Image.new("RGB", (800, 480), "white")
        bitmap = pil_to_1bit_bitmap(image)
        assert isinstance(bitmap, bytes)

    def test_white_image_produces_all_ones(self):
        """White image should produce all 0xFF bytes (1 = white in e-ink)"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap

        image = Image.new("RGB", (800, 480), "white")
        bitmap = pil_to_1bit_bitmap(image, dither="none")
        # All bytes should be 0xFF (all 1s = all white pixels)
        assert all(b == 0xFF for b in bitmap)

    def test_black_image_produces_all_zeros(self):
        """Black image should produce all 0x00 bytes (0 = black in e-ink)"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap

        image = Image.new("RGB", (800, 480), "black")
        bitmap = pil_to_1bit_bitmap(image, dither="none")
        # All bytes should be 0x00 (all 0s = all black pixels)
        assert all(b == 0x00 for b in bitmap)

    def test_invert_swaps_black_and_white(self):
        """Invert parameter should swap black and white"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap

        image = Image.new("RGB", (800, 480), "white")
        bitmap_normal = pil_to_1bit_bitmap(image, dither="none", invert=False)
        bitmap_inverted = pil_to_1bit_bitmap(image, dither="none", invert=True)

        # Normal white should be 0xFF, inverted should be 0x00
        assert bitmap_normal[0] == 0xFF
        assert bitmap_inverted[0] == 0x00

    def test_dither_floyd_steinberg_works(self):
        """Floyd-Steinberg dithering should produce different output than no dither"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap

        # Create a gray image (50% gray)
        image = Image.new("RGB", (800, 480), (128, 128, 128))
        bitmap_none = pil_to_1bit_bitmap(image, dither="none")
        bitmap_fs = pil_to_1bit_bitmap(image, dither="floyd-steinberg")

        # Dithered output should have a mix of 0s and 1s (not all same byte)
        # While no-dither on gray might be all one value
        assert bitmap_none != bitmap_fs

    def test_accepts_grayscale_image(self):
        """Converter should accept grayscale (L mode) images"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap

        image = Image.new("L", (800, 480), 255)  # White grayscale
        bitmap = pil_to_1bit_bitmap(image, dither="none")
        assert len(bitmap) == 48000
        assert all(b == 0xFF for b in bitmap)

    def test_accepts_rgba_image(self):
        """Converter should accept RGBA images"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap

        image = Image.new("RGBA", (800, 480), (255, 255, 255, 255))
        bitmap = pil_to_1bit_bitmap(image, dither="none")
        assert len(bitmap) == 48000

    def test_resizes_non_standard_dimensions(self):
        """Converter should resize images that don't match 800x480"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap

        image = Image.new("RGB", (1600, 960), "white")  # Double size
        bitmap = pil_to_1bit_bitmap(image)
        assert len(bitmap) == 48000  # Still correct output size

    def test_checkerboard_pattern(self):
        """Alternating pixel pattern should produce correct byte pattern"""
        from src.display.bitmap_converter import pil_to_1bit_bitmap

        # Create 8x1 image with alternating pixels: B W B W B W B W
        image = Image.new("1", (800, 480), 0)  # Start black
        pixels = image.load()
        # Set every other pixel to white in first row
        for x in range(0, 800, 2):
            pixels[x, 0] = 1  # White

        bitmap = pil_to_1bit_bitmap(image, dither="none")
        # First byte of first row: pixels 0-7 = W B W B W B W B = 10101010 = 0xAA
        assert bitmap[0] == 0xAA


class TestBitmapConverterHash:
    """Test content hashing for ETag generation"""

    def test_calculate_hash_returns_string(self):
        """Hash function should return a string"""
        from src.display.bitmap_converter import calculate_bitmap_hash

        data = b"\x00" * 100
        hash_value = calculate_bitmap_hash(data)
        assert isinstance(hash_value, str)

    def test_same_content_same_hash(self):
        """Same content should produce same hash"""
        from src.display.bitmap_converter import calculate_bitmap_hash

        data = b"\x00\xFF" * 50
        hash1 = calculate_bitmap_hash(data)
        hash2 = calculate_bitmap_hash(data)
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """Different content should produce different hash"""
        from src.display.bitmap_converter import calculate_bitmap_hash

        hash1 = calculate_bitmap_hash(b"\x00" * 100)
        hash2 = calculate_bitmap_hash(b"\xFF" * 100)
        assert hash1 != hash2
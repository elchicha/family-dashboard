# src/display/bitmap_converter.py
from PIL import Image
import hashlib


def pil_to_1bit_bitmap(image, dither="floyd-steinberg", invert=False):
    """
    Convert PIL image to 1-bit bitmap for e-ink display.

    Args:
        image: PIL Image object
        dither: "none" or "floyd-steinberg"
        invert: If True, swap black and white

    Returns:
        bytes: 1-bit bitmap data (800*480/8 = 48000 bytes)
    """
    # Resize to 800x480 if needed
    if image.size != (800, 480):
        image = image.resize((800, 480), Image.Resampling.LANCZOS)

    # Convert to grayscale first
    if image.mode != "L":
        image = image.convert("L")

    # Convert to 1-bit (black and white)
    if dither == "none":
        image = image.convert("1", dither=Image.Dither.NONE)
    else:  # floyd-steinberg
        image = image.convert("1", dither=Image.Dither.FLOYDSTEINBERG)

    # Get pixel data
    pixels = list(image.getdata())

    # Pack into bytes (8 pixels per byte)
    bitmap = bytearray()
    for i in range(0, len(pixels), 8):
        byte = 0
        for bit in range(8):
            if i + bit < len(pixels):
                pixel_value = pixels[i + bit]
                # In PIL '1' mode: 0=black, 255=white
                # We want: 1=white, 0=black
                if pixel_value > 0:  # White pixel
                    if not invert:
                        byte |= 1 << (7 - bit)
                else:  # Black pixel
                    if invert:
                        byte |= 1 << (7 - bit)
        bitmap.append(byte)

    return bytes(bitmap)


def calculate_bitmap_hash(data):
    """Calculate SHA-256 hash of bitmap data for ETag"""
    return hashlib.sha256(data).hexdigest()

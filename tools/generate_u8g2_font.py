#!/usr/bin/env python3
"""
Generate U8g2-format subset fonts from a TTF/TTC font using Pillow.

Reads the codepoint map files produced by generate_font_subset.py and renders
only those glyphs into a U8g2 binary font array. The output is a C header file
that LovyanGFX can use via lgfx::U8g2font.

Usage:
    python3 generate_u8g2_font.py

Requires: Pillow (pip3 install Pillow)

The U8g2 font format is documented at:
    https://github.com/olikraus/u8g2/wiki/u8g2fontformat
"""

import os
import struct
import sys
from PIL import ImageFont, Image, ImageDraw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
I18N_DIR = os.path.join(PROJECT_DIR, "src", "i18n_engine", "fonts")

# System CJK font (macOS Hiragino Sans GB covers both CN and JP)
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"

# Sizes to generate (mapped to FreeSans equivalents)
FONT_SIZES = [14, 20, 28]


def load_codepoints(map_path):
    """Load codepoints from a .map file (ranges like '32-126' and individual '$XXXX')."""
    codepoints = []
    with open(map_path, "r") as f:
        for line in f:
            line = line.strip().rstrip(",")
            if line.startswith("$"):
                cp = int(line[1:], 16)
                codepoints.append(cp)
            elif "-" in line:
                parts = line.split("-")
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    for cp in range(int(parts[0]), int(parts[1]) + 1):
                        codepoints.append(cp)
    return sorted(set(codepoints))


def render_glyph(font, char, pixel_size):
    """Render a single character to a bitmap and return glyph metrics + bitmap data."""
    # Create image large enough for the glyph
    img = Image.new("L", (pixel_size * 3, pixel_size * 3), 0)
    draw = ImageDraw.Draw(img)

    # Draw at offset to capture descenders
    origin_x = pixel_size
    origin_y = pixel_size
    draw.text((origin_x, origin_y), char, font=font, fill=255)

    # Get actual bounding box of non-zero pixels
    bbox = img.getbbox()
    if bbox is None:
        # Empty glyph (space, etc.)
        advance = font.getlength(char)
        return {
            "width": 0, "height": 0,
            "xoffset": 0, "yoffset": 0,
            "advance": int(advance),
            "bitmap": b"",
        }

    x0, y0, x1, y1 = bbox
    glyph_w = x1 - x0
    glyph_h = y1 - y0
    xoffset = x0 - origin_x
    yoffset = y0 - origin_y

    advance = int(font.getlength(char))

    # Extract bitmap (1 bit per pixel, packed into bytes, MSB first)
    bitmap_bits = []
    for row in range(y0, y1):
        for col in range(x0, x1):
            pixel = img.getpixel((col, row))
            bitmap_bits.append(1 if pixel > 127 else 0)

    # Pack bits into bytes
    bitmap_bytes = bytearray()
    for i in range(0, len(bitmap_bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bitmap_bits) and bitmap_bits[i + j]:
                byte |= (1 << (7 - j))
        bitmap_bytes.append(byte)

    return {
        "width": glyph_w,
        "height": glyph_h,
        "xoffset": xoffset,
        "yoffset": yoffset,
        "advance": advance,
        "bitmap": bytes(bitmap_bytes),
    }


def build_u8g2_font(font_path, pixel_size, codepoints):
    """Build a U8g2-format font byte array for the given codepoints.

    The U8g2 font format uses a simplified structure:
    - 23-byte header with font metrics
    - Glyph data grouped by Unicode ranges
    - Each glyph: encoding(2) + metrics + bitmap data
    """
    font = ImageFont.truetype(font_path, pixel_size)

    # Compute font-wide metrics
    ascent = pixel_size  # approximate
    descent = pixel_size // 4

    # Render all glyphs
    glyphs = {}
    for cp in codepoints:
        ch = chr(cp)
        try:
            glyph = render_glyph(font, ch, pixel_size)
            glyphs[cp] = glyph
        except Exception:
            pass

    if not glyphs:
        return b""

    # Compute actual ascent/descent from rendered glyphs
    max_above = 0
    max_below = 0
    max_advance = 0
    for cp, g in glyphs.items():
        if g["height"] > 0:
            top = -g["yoffset"]
            bottom = g["yoffset"] + g["height"]
            if top > max_above:
                max_above = top
            if bottom > max_below:
                max_below = bottom
        if g["advance"] > max_advance:
            max_advance = g["advance"]

    ascent = max_above
    descent = max_below

    # Build U8g2 font data
    # Format: header(23 bytes) + glyph_count(2) + glyph_data...
    # Simplified format compatible with LovyanGFX U8g2font

    # Group codepoints into ranges for the U8g2 lookup table
    # For simplicity, use format 1 (unsorted, linear search)
    # This avoids the complex range-based lookup table

    # Actually, LovyanGFX uses the standard U8g2 font format.
    # The simplest approach is to use format 0 (glyph data sorted by encoding).
    # U8g2 font header (23 bytes):
    #   [0] glyph_cnt (number of glyphs in range 0-255)
    #   [1] unicode_last_0 (last unicode glyph)
    #   [2-3] unicode range start/end bytes
    #   ... many header fields

    # This format is complex. Instead, let me output a simpler format that
    # LovyanGFX's U8g2font class can parse. Looking at the LovyanGFX source:
    # lgfx::U8g2font parses the standard u8g2 font byte array.

    # The u8g2 font format header is:
    #  byte 0: glyph_cnt (glyphs in range 0x20-0xFF)
    #  byte 1: unicode_last_0 (last char code in basic range, typically 0x7F or 0xFF)
    #  byte 2-3: (uint16) start position of unicode lookup table
    #  byte 4: (int8) ascent_A (capital letter height)
    #  byte 5: (int8) descent_g (lowercase descender depth, negative)
    #  byte 6: (int8) ascent_para (ascent for parenthesis)
    #  byte 7: (int8) descent_para (descent for parenthesis)
    #  byte 8-9: (uint16) start position of uppercase A
    #  byte 10-11: (uint16) start position of lowercase a
    #  byte 12: (uint8) bits_per_0
    #  byte 13: (uint8) bits_per_1
    #  byte 14: (uint8) bits_per_char_width
    #  byte 15: (uint8) bits_per_char_height
    #  byte 16: (uint8) bits_per_char_x
    #  byte 17: (uint8) bits_per_char_y
    #  byte 18: (uint8) bits_per_delta_x
    #  byte 19-20: (int16) max_char_width
    #  byte 21-22: (int16) max_char_height

    # This is getting very complex. Let me use a different, simpler approach:
    # Generate the font using the existing efont data by extracting only needed glyphs.

    return None  # Signal to use the extraction approach instead


def extract_from_existing_efont(lang_code, codepoints, sizes):
    """
    Instead of generating fonts from scratch, this approach would parse
    the existing lgfx_efont_XX.c files and extract only the needed glyphs.

    However, the U8g2 binary format is not trivially parseable for extraction.

    The recommended approach is to install bdfconv and use the map files
    generated by generate_font_subset.py.
    """
    pass


def generate_vlw_font(font_path, pixel_size, codepoints, output_name):
    """Generate a VLW (LGFX native) font instead of U8g2.

    VLW is LovyanGFX's native smooth font format, much simpler than U8g2.
    It stores anti-aliased glyph bitmaps with a simple header.

    LovyanGFX can load VLW fonts via loadFont() from a header array.
    """
    font = ImageFont.truetype(font_path, pixel_size)

    # VLW format:
    # Header: 6 x uint32_t (big-endian)
    #   [0] glyph_count
    #   [1] version (always 0x0B)
    #   [2] font_size
    #   [3] padding (0)
    #   [4] ascent
    #   [5] descent
    #
    # Then for each glyph:
    #   uint32_t unicode
    #   uint32_t height
    #   uint32_t width
    #   uint32_t xAdvance
    #   uint32_t topExtent (dy from baseline to top)
    #   uint32_t leftExtent (dx from origin to left edge)
    #   uint8_t bitmap[width * height]  (alpha values, 0-255)

    rendered = []
    for cp in codepoints:
        ch = chr(cp)
        try:
            # Render anti-aliased
            size_factor = 1
            img = Image.new("L", (pixel_size * 3, pixel_size * 3), 0)
            draw = ImageDraw.Draw(img)
            ox, oy = pixel_size, pixel_size
            draw.text((ox, oy), ch, font=font, fill=255)

            bbox = img.getbbox()
            if bbox is None:
                # Space or empty glyph
                advance = int(font.getlength(ch))
                rendered.append({
                    "unicode": cp, "width": 0, "height": 0,
                    "xAdvance": advance, "topExtent": 0, "leftExtent": 0,
                    "bitmap": b"",
                })
                continue

            x0, y0, x1, y1 = bbox
            w = x1 - x0
            h = y1 - y0
            advance = int(font.getlength(ch))
            top_extent = oy - y0  # distance from baseline to top of glyph
            left_extent = x0 - ox  # left bearing

            # Extract alpha bitmap
            bmp = bytearray()
            for row in range(y0, y1):
                for col in range(x0, x1):
                    bmp.append(img.getpixel((col, row)))

            rendered.append({
                "unicode": cp, "width": w, "height": h,
                "xAdvance": advance, "topExtent": top_extent,
                "leftExtent": left_extent,
                "bitmap": bytes(bmp),
            })
        except Exception as e:
            print(f"  Warning: failed to render U+{cp:04X}: {e}")

    if not rendered:
        return None

    # Compute font metrics
    max_ascent = max((g["topExtent"] for g in rendered if g["height"] > 0), default=pixel_size)
    max_descent = max(
        (g["height"] - g["topExtent"] for g in rendered if g["height"] > 0),
        default=pixel_size // 4,
    )

    # Build VLW binary
    data = bytearray()

    # Header (6 x uint32 big-endian)
    data += struct.pack(">I", len(rendered))  # glyph count
    data += struct.pack(">I", 0x0B)  # version
    data += struct.pack(">I", pixel_size)  # font size
    data += struct.pack(">I", 0)  # padding
    data += struct.pack(">I", max(0, max_ascent))  # ascent
    data += struct.pack(">I", max(0, max_descent))  # descent

    # Glyph metrics (28 bytes per glyph header)
    for g in rendered:
        data += struct.pack(">I", g["unicode"])
        data += struct.pack(">I", g["height"])
        data += struct.pack(">I", g["width"])
        data += struct.pack(">I", g["xAdvance"])
        data += struct.pack(">i", g["topExtent"])   # signed
        data += struct.pack(">i", g["leftExtent"])  # signed
        data += struct.pack(">I", 0)  # padding

    # Glyph bitmaps (alpha channel, 1 byte per pixel)
    for g in rendered:
        data += g["bitmap"]

    return bytes(data)


def write_c_header(data, output_path, array_name):
    """Write font data as a C header with a PROGMEM const uint8_t array."""
    with open(output_path, "w") as f:
        f.write("#pragma once\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write(f"// Auto-generated by generate_u8g2_font.py\n")
        f.write(f"// Size: {len(data)} bytes ({len(data) / 1024:.1f} KB)\n\n")
        f.write("#include <pgmspace.h>\n\n")
        f.write(f"PROGMEM const uint8_t {array_name}[] = {{\n")

        for i in range(0, len(data), 16):
            chunk = data[i : i + 16]
            hex_values = ", ".join(f"0x{b:02X}" for b in chunk)
            f.write(f"    {hex_values},\n")

        f.write("};\n")


LANGUAGES = ["es", "vi"]  # CN/JA use pre-built U8g2 fonts, not regenerated


def main():
    # Check font availability
    if not os.path.exists(FONT_PATH):
        print(f"Error: Font not found at {FONT_PATH}")
        print("On macOS, Hiragino Sans GB should be available by default.")
        sys.exit(1)

    # Load codepoints for each language
    lang_cps = {}
    for lang in LANGUAGES:
        map_path = os.path.join(SCRIPT_DIR, f"{lang}_subset.map")
        if not os.path.exists(map_path):
            print(f"Warning: {map_path} not found, skipping {lang}")
            continue
        lang_cps[lang] = load_codepoints(map_path)
        print(f"{lang.upper()}: {len(lang_cps[lang])} codepoints")

    if not lang_cps:
        print("Error: Run generate_font_subset.py first to create .map files")
        sys.exit(1)

    print(f"\nFont: {FONT_PATH}")
    print()

    for size in FONT_SIZES:
        print(f"Generating size {size}px...")
        for lang, cps in lang_cps.items():
            data = generate_vlw_font(FONT_PATH, size, cps, f"fonts_{lang}_{size}")
            if data:
                path = os.path.join(I18N_DIR, f"font_{lang}_{size}.h")
                write_c_header(data, path, f"font_{lang}_{size}")
                print(f"  {lang.upper()}: {len(data)} bytes -> {path}")

    print()
    print("Font headers generated in ICB/i18n/")
    total = 0
    for size in FONT_SIZES:
        for lang in lang_cps:
            path = os.path.join(I18N_DIR, f"font_{lang}_{size}.h")
            if os.path.exists(path):
                total += os.path.getsize(path)
    print(f"  Header text: {total / 1024:.1f} KB (binary data ~{total / 5 / 1024:.1f} KB in flash)")


if __name__ == "__main__":
    main()

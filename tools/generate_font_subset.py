#!/usr/bin/env python3
"""
Generate font subset map files for CJK translations.

This script reads the Chinese and Japanese translation headers, extracts all
unique Unicode codepoints (above ASCII), and generates .map files compatible
with the u8g2 bdfconv tool.

Usage:
    python3 generate_font_subset.py

Output:
    tools/cn_subset.map   — codepoint map for Chinese subset font
    tools/ja_subset.map   — codepoint map for Japanese subset font

To generate the actual U8g2 font files, use bdfconv:
    1. Get a CJK BDF font (e.g., from efont project or via otf2bdf)
    2. Build bdfconv from https://github.com/olikraus/u8g2/tree/master/tools/font/bdfconv
    3. Run:
       bdfconv -v -b 0 -f 1 -M cn_subset.map source_cn.bdf -o fonts_cn_subset_16.c -n fonts_cn_subset_16
       bdfconv -v -b 0 -f 1 -M ja_subset.map source_ja.bdf -o fonts_ja_subset_16.c -n fonts_ja_subset_16

    The output .c files contain PROGMEM uint8_t arrays that LovyanGFX can use
    directly as U8g2 fonts via lgfx::U8g2font.
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
I18N_DIR = os.path.join(PROJECT_DIR, "ICB", "i18n")


def extract_codepoints_from_header(filepath):
    """Extract all Unicode codepoints from a translation header file.

    Parses UTF-8 hex escape sequences (\\xNN) and plain ASCII from the
    string literals in the translation arrays.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all string literals (between quotes)
    strings = re.findall(r'"([^"]*)"', content)

    codepoints = set()
    for s in strings:
        # Decode C escape sequences: \xNN
        try:
            decoded = s.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            # Fallback: process raw hex escapes manually
            decoded = decode_hex_escapes(s)

        for ch in decoded:
            cp = ord(ch)
            if cp > 127:  # Only non-ASCII
                codepoints.add(cp)

    return codepoints


def decode_hex_escapes(s):
    """Decode \\xNN hex escape sequences in a C string literal."""
    result = bytearray()
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "x":
            # Read hex bytes
            hex_str = s[i + 2 : i + 4]
            if len(hex_str) == 2:
                result.append(int(hex_str, 16))
                i += 4
                continue
        result.append(ord(s[i]))
        i += 1
    try:
        return result.decode("utf-8")
    except UnicodeDecodeError:
        return result.decode("utf-8", errors="replace")


def generate_map_file(codepoints, output_path, language_name):
    """Generate a bdfconv-compatible .map file.

    Format: ranges like "32-255," and individual "$XXXX," entries.
    bdfconv treats 0x00-0xFF as the base glyph table and 0x100+ as Unicode.
    Latin-1 chars (0x80-0xFF) must be in the base range, not as $00XX entries.
    """
    all_cps = set(range(32, 127))
    all_cps.update(codepoints)

    # Split: base range (0-255) vs Unicode (256+)
    has_latin1 = any(0x80 <= cp <= 0xFF for cp in codepoints)
    unicode_cps = sorted(cp for cp in codepoints if cp >= 0x100)

    with open(output_path, "w") as f:
        # Base range: include 32-255 if any Latin-1 chars needed, else just 32-126
        if has_latin1:
            f.write("32-255,\n")
        else:
            f.write("32-126,\n")

        # Unicode codepoints (0x100+) individually
        for cp in unicode_cps:
            f.write(f"${cp:04X},\n")

    return len(all_cps), len(codepoints)


LANGUAGES = {
    "cn": ("strings_cn.h", "Chinese Simplified"),
    "ja": ("strings_ja.h", "Japanese"),
    "es": ("strings_es.h", "Spanish"),
    "vi": ("strings_vi.h", "Vietnamese"),
}


def main():
    for lang_code, (filename, display_name) in LANGUAGES.items():
        filepath = os.path.join(I18N_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, skipping {display_name}")
            continue

        cps = extract_codepoints_from_header(filepath)
        map_path = os.path.join(SCRIPT_DIR, f"{lang_code}_subset.map")
        total, extra = generate_map_file(cps, map_path, display_name)

        print(f"{display_name} subset: {extra} non-ASCII codepoints + 95 ASCII = {total} total")
        print(f"  Map file: {map_path}")
        sample = ", ".join(f"U+{cp:04X} ({chr(cp)})" for cp in sorted(cps)[:10])
        print(f"  Sample: {sample}")
        print()


if __name__ == "__main__":
    main()

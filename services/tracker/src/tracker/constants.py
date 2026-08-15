import struct
import zlib

TRANSPARENT_1X1_GIF = (
    b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff"
    b"\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00"
    b"\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
)

TRANSPARENT_1X1_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

TRANSPARENT_1X1_WEBP = (
    b"RIFF\x1a\x00\x00\x00WEBPVP8L\x0e\x00\x00\x00"
    b"/\x00\x00\x00\x00\x07\x88\x81\x08\x00\x00\x01\x00\x00"
)


def _make_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


def build_dynamic_png(token: str) -> bytes:
    """Generate a valid 1x1 transparent PNG with authentic sRGB/gAMA color space
    and asset metadata.
    """
    header = b"\x89PNG\r\n\x1a\n"
    # IHDR: 1x1, 8-bit, RGBA (color_type=6)
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    ihdr_chunk = _make_png_chunk(b"IHDR", ihdr_data)

    # sRGB chunk (Perceptual rendering intent)
    srgb_chunk = _make_png_chunk(b"sRGB", b"\x00")

    # gAMA chunk (standard 45455 = 1/2.2 gamma)
    gama_chunk = _make_png_chunk(b"gAMA", struct.pack(">I", 45455))

    # Software metadata chunk (Figma / Adobe UI asset signature)
    software_chunk = _make_png_chunk(b"tEXt", b"Software\0Figma Asset Exporter v12")

    # tEXt chunk: Asset-ID
    text_data = b"Asset-ID\0" + token.encode("utf-8")
    text_chunk = _make_png_chunk(b"tEXt", text_data)

    # IDAT: 1 scanline (filter 0 + RGBA 0,0,0,0)
    raw_scanline = b"\x00\x00\x00\x00\x00"
    compressed = zlib.compress(raw_scanline)
    idat_chunk = _make_png_chunk(b"IDAT", compressed)

    # IEND
    iend_chunk = _make_png_chunk(b"IEND", b"")

    return (
        header
        + ihdr_chunk
        + srgb_chunk
        + gama_chunk
        + software_chunk
        + text_chunk
        + idat_chunk
        + iend_chunk
    )


TRANSPARENT_1X1_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1" '
    b'viewBox="0 0 1 1" opacity="0.01"></svg>'
)


def build_dynamic_svg(token: str) -> bytes:
    """Generate an adaptive dark-mode vector SVG with embedded asset token metadata."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1" viewBox="0 0 1 1">\n'
        "  <style>\n"
        "    :root { color-scheme: light dark; }\n"
        "    @media (prefers-color-scheme: dark) { rect { fill: transparent !important; } }\n"
        "  </style>\n"
        f"  <!-- asset-id: {token} -->\n"
        '  <rect width="1" height="1" fill="transparent" opacity="0.01" />\n'
        "</svg>"
    ).encode("utf-8")

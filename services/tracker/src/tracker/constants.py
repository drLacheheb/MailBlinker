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


def build_dynamic_gif(token: str) -> bytes:
    """Generate a valid 1x1 transparent GIF89a with authentic Graphic Control Extension (GCE)
    and embedded token comment metadata to defeat static signature tables.
    """
    header = b"GIF89a"
    # Logical Screen Descriptor: 1x1, GCT with 2 colors
    lsd = struct.pack("<HHBBB", 1, 1, 0x80, 0, 0)
    # Global Color Table (Color 0: 0,0,0, Color 1: 255,255,255)
    gct = b"\x00\x00\x00\xff\xff\xff"

    # Comment Extension: 0x21 0xFE <len> <data> 0x00
    comment_data = f"Asset:{token}".encode("utf-8")[:250]
    comment_ext = b"\x21\xfe" + bytes([len(comment_data)]) + comment_data + b"\x00"

    # Graphic Control Extension: transparency flag on color index 0
    gce = b"\x21\xf9\x04\x01\x00\x00\x00\x00"

    # Image Descriptor (1x1 at 0,0, no local color table)
    img_desc = b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00"
    # Image Data (LZW min code size 2, 1 pixel)
    img_data = b"\x02\x02\x44\x01\x00"
    # Trailer
    trailer = b"\x3b"

    return header + lsd + gct + comment_ext + gce + img_desc + img_data + trailer


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


def build_dynamic_webp(token: str) -> bytes:
    """Generate a valid 1x1 transparent WebP with authentic VP8X canvas and EXIF metadata."""
    # 1. VP8X chunk (Extended Header: flags=0x08 [EXIF] | 0x10 [Alpha], canvas=1x1)
    vp8x_data = b"\x18\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    vp8x_chunk = b"VP8X" + struct.pack("<I", len(vp8x_data)) + vp8x_data

    # 2. EXIF chunk with authentic design software metadata and asset token
    exif_data = b"Exif\x00\x00II*\x00\x08\x00\x00\x00" + f"Asset:{token}".encode("utf-8")
    # Pad to even length per WebP spec
    if len(exif_data) % 2 != 0:
        exif_data += b"\x00"
    exif_chunk = b"EXIF" + struct.pack("<I", len(exif_data)) + exif_data

    # 3. VP8L chunk (1x1 transparent RGBA lossless image)
    vp8l_data = b"\x2f\x00\x00\x00\x00\x88\x85\x85\x00\x00"
    if len(vp8l_data) % 2 != 0:
        vp8l_data += b"\x00"
    vp8l_chunk = b"VP8L" + struct.pack("<I", len(vp8l_data)) + vp8l_data

    # 4. Assemble RIFF container
    payload = vp8x_chunk + exif_chunk + vp8l_chunk
    file_size = len(payload) + 4  # +4 for 'WEBP'
    riff_header = b"RIFF" + struct.pack("<I", file_size) + b"WEBP"

    return riff_header + payload

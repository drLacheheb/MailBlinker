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
    """Generate a valid 1x1 transparent PNG with a unique cryptographic checksum."""
    header = b"\x89PNG\r\n\x1a\n"
    # IHDR: 1x1, 8-bit, RGBA (color_type=6)
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    ihdr_chunk = _make_png_chunk(b"IHDR", ihdr_data)

    # tEXt chunk: keyword\0text (embeds unique token metadata for unique SHA-256)
    text_data = b"Asset-ID\0" + token.encode("utf-8")
    text_chunk = _make_png_chunk(b"tEXt", text_data)

    # IDAT: 1 scanline (filter 0 + RGBA 0,0,0,0)
    raw_scanline = b"\x00\x00\x00\x00\x00"
    compressed = zlib.compress(raw_scanline)
    idat_chunk = _make_png_chunk(b"IDAT", compressed)

    # IEND
    iend_chunk = _make_png_chunk(b"IEND", b"")

    return header + ihdr_chunk + text_chunk + idat_chunk + iend_chunk

#!/usr/bin/env python3
"""
Builds the SmartX icon set from geometry, not from a photograph of a logo.

## Plain version

The old icon was a deep purple mark on black. At 16 pixels, which is the size a browser tab
actually shows, that is two dark colours against each other and it turned to mud. The owner said
so on 22 September: "the current favcon is not clear enough". The new mark is the other way
round, a near black mark on light lavender, which holds its shape when it is tiny.

This draws the mark from coordinates rather than shrinking an image, so every size is sharp
instead of blurry. It writes the SVG that modern browsers prefer, the PNG sizes older ones want,
and the .ico that Windows and some crawlers still ask for.

Run it with `python3 tools/make-favicon.py`. It uses only the Python standard library, so it runs
anywhere without ImageMagick, Pillow or a headless browser. That is deliberate: a build step that
needs tools a machine may not have is a build step that quietly stops being run.

Colours are the ones already in the product, not new ones:
  #C9A6FF  the light lavender, already in web/console.html
  #120C1C  the near black, already in web/console.html and the website
"""

import struct
import zlib
from pathlib import Path

LAVENDER = (0xC9, 0xA6, 0xFF)
INK = (0x12, 0x0C, 0x1C)

# The mark, on a 180 by 180 grid so the numbers read like the artwork they came from.
# A square bracket each side of a filled dot. Chunky on purpose: thin strokes vanish at 16px.
GRID = 180.0
CORNER = 40.0          # rounded square, about 22 percent, matching the source
BAR = 13.0             # stroke width of the brackets
TOP, BOT = 52.0, 128.0  # vertical extent of the brackets
L_OUT, L_IN = 44.0, 82.0    # left bracket: outer edge and how far its arms reach in
R_IN, R_OUT = 98.0, 136.0   # right bracket
DOT_R = 17.0
CX = CY = 90.0


def inside(x: float, y: float) -> bool:
    """Is this point part of the black mark? Coordinates are on the 180 grid."""
    # The dot.
    if (x - CX) ** 2 + (y - CY) ** 2 <= DOT_R ** 2:
        return True
    # Left bracket: the upright, plus the top and bottom arms.
    if L_OUT <= x <= L_OUT + BAR and TOP <= y <= BOT:
        return True
    if L_OUT <= x <= L_IN and (TOP <= y <= TOP + BAR or BOT - BAR <= y <= BOT):
        return True
    # Right bracket, mirrored.
    if R_OUT - BAR <= x <= R_OUT and TOP <= y <= BOT:
        return True
    if R_IN <= x <= R_OUT and (TOP <= y <= TOP + BAR or BOT - BAR <= y <= BOT):
        return True
    return False


def in_rounded_square(x: float, y: float) -> bool:
    """The lavender tile itself, so the corners are round rather than square."""
    for cx, cy in ((CORNER, CORNER), (GRID - CORNER, CORNER),
                   (CORNER, GRID - CORNER), (GRID - CORNER, GRID - CORNER)):
        near_x = x < CORNER if cx == CORNER else x > GRID - CORNER
        near_y = y < CORNER if cy == CORNER else y > GRID - CORNER
        if near_x and near_y:
            return (x - cx) ** 2 + (y - cy) ** 2 <= CORNER ** 2
    return True


def render(size: int, supersample: int = 4, square: bool = False) -> bytes:
    """RGBA pixels, anti-aliased by sampling each pixel several times and averaging."""
    rows = bytearray()
    step = GRID / (size * supersample)
    half = step / 2
    for py in range(size):
        rows.append(0)  # PNG filter byte: none
        for px in range(size):
            r = g = b = a = 0
            for sy in range(supersample):
                for sx in range(supersample):
                    x = (px * supersample + sx) * step + half
                    y = (py * supersample + sy) * step + half
                    if not square and not in_rounded_square(x, y):
                        continue  # transparent outside the tile
                    col = INK if inside(x, y) else LAVENDER
                    r += col[0]; g += col[1]; b += col[2]; a += 255
            n = supersample * supersample
            if a == 0:
                rows += bytes((0, 0, 0, 0))
            else:
                lit = a // 255  # samples that landed on the tile
                rows += bytes((r // lit, g // lit, b // lit, a // n))
    return bytes(rows)


def png(size: int, square: bool = False) -> bytes:
    """A PNG, written by hand. zlib is in the standard library; nothing else is needed."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8 bit RGBA
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(render(size, square=square), 9)) + chunk(b"IEND", b""))


def ico(sizes: list[int]) -> bytes:
    """An .ico carrying PNGs, which every browser since Vista reads."""
    images = [png(s) for s in sizes]
    head = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries, body = b"", b""
    for s, data in zip(sizes, images):
        entries += struct.pack("<BBBBHHII", s if s < 256 else 0, s if s < 256 else 0,
                               0, 0, 1, 32, len(data), offset)
        offset += len(data)
        body += data
    return head + entries + body


SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 180" role="img" aria-label="SmartX">
  <rect width="180" height="180" rx="{CORNER:g}" fill="#{LAVENDER[0]:02X}{LAVENDER[1]:02X}{LAVENDER[2]:02X}"/>
  <g fill="#{INK[0]:02X}{INK[1]:02X}{INK[2]:02X}">
    <rect x="{L_OUT:g}" y="{TOP:g}" width="{BAR:g}" height="{BOT - TOP:g}"/>
    <rect x="{L_OUT:g}" y="{TOP:g}" width="{L_IN - L_OUT:g}" height="{BAR:g}"/>
    <rect x="{L_OUT:g}" y="{BOT - BAR:g}" width="{L_IN - L_OUT:g}" height="{BAR:g}"/>
    <rect x="{R_OUT - BAR:g}" y="{TOP:g}" width="{BAR:g}" height="{BOT - TOP:g}"/>
    <rect x="{R_IN:g}" y="{TOP:g}" width="{R_OUT - R_IN:g}" height="{BAR:g}"/>
    <rect x="{R_IN:g}" y="{BOT - BAR:g}" width="{R_OUT - R_IN:g}" height="{BAR:g}"/>
    <circle cx="{CX:g}" cy="{CY:g}" r="{DOT_R:g}"/>
  </g>
</svg>
"""

if __name__ == "__main__":
    here = Path(__file__).resolve().parent.parent
    assets = here / "assets"
    assets.mkdir(exist_ok=True)
    (here / "favicon.svg").write_text(SVG)
    (here / "favicon.ico").write_bytes(ico([16, 32, 48]))
    for s, name, square in ((16, "favicon-16.png", False), (32, "favicon-32.png", False),
                            # Square and opaque on purpose: iOS paints the transparent part of a
                            # home screen icon BLACK and applies its own mask, which bulges past a
                            # round corner, so a rounded tile shows black slivers. Apple asks for a
                            # square icon and does the rounding itself.
                            (180, "apple-touch-icon.png", True),
                            (192, "icon-192.png", False), (512, "icon-512.png", False)):
        (assets / name).write_bytes(png(s, square=square))
        print(f"  wrote assets/{name}")
    print("  wrote favicon.svg and favicon.ico")

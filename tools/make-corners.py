#!/usr/bin/env python3
"""Generate rounded xfwm4 title-bar corners for PRO-dark-XFCE-4.20.

Rewrites top-{left,right}-{active,inactive,active-shaded}.xpm as anti-aliased
quarter circles. Each row takes its colour from column 0 of the matching
title-1-*.xpm, so the corners blend into the title gradient. XPM has no
partial alpha: pixels less than half covered are transparent, partly covered
pixels are mixed toward the frame edge colour.

Usage: tools/make-corners.py [--radius 10] [--xfwm-dir PRO-dark-XFCE-4.20/xfwm4]
"""
import argparse
import re
from pathlib import Path

EDGE = "#7e8185"          # frame edge colour used to soften the arc
SAMPLES = 4               # 4x4 supersampling per pixel
SOURCES = {"active": "title-1-active", "inactive": "title-1-inactive",
           "active-shaded": "title-1-active-shaded"}
# Printable XPM palette characters (no space, quote or backslash).
ALPHABET = "".join(chr(c) for c in range(33, 127) if chr(c) not in '"\\')


def read_xpm(path):
    """Return (width, height, rows) with pixels as '#rrggbb' or None."""
    strings = re.findall(r'"((?:[^"\\]|\\.)*)"', Path(path).read_text())
    width, height, ncolors, cpp = map(int, strings[0].split()[:4])
    palette = {}
    for entry in strings[1:1 + ncolors]:
        key, spec = entry[:cpp], entry[cpp:].split()
        value = spec[spec.index("c") + 1]
        palette[key] = None if value.lower() == "none" else value.lower()
    rows = [[palette[row[x * cpp:(x + 1) * cpp]] for x in range(width)]
            for row in strings[1 + ncolors:1 + ncolors + height]]
    return width, height, rows


def write_xpm(path, var_name, pixels):
    """Write pixels ('#rrggbb' or None) as a deterministic one-char-per-pixel XPM."""
    colours = sorted({p for row in pixels for p in row if p is not None})
    if len(colours) > len(ALPHABET):
        raise ValueError(f"too many colours: {len(colours)}")
    key = {None: " ", **{c: ALPHABET[i] for i, c in enumerate(colours)}}
    height, width = len(pixels), len(pixels[0])
    has_none = any(p is None for row in pixels for p in row)
    lines = [f"{width} {height} {len(colours) + has_none} 1"]
    if has_none:
        lines.append("  c None")
    lines += [f"{key[c]}\tc {c.upper()}" for c in colours]
    lines += ["".join(key[p] for p in row) for row in pixels]
    body = ",\n".join(f'"{line}"' for line in lines)
    Path(path).write_text(f"/* XPM */\nstatic char * {var_name}[] = {{\n{body}}};\n")


def coverage(x, y, radius):
    """Fraction of pixel (x, y) inside a top-left quarter circle of the given radius."""
    if x >= radius or y >= radius:
        return 1.0
    inside = 0
    for i in range(SAMPLES):
        for j in range(SAMPLES):
            sx = x + (i + 0.5) / SAMPLES
            sy = y + (j + 0.5) / SAMPLES
            inside += (sx - radius) ** 2 + (sy - radius) ** 2 <= radius ** 2
    return inside / SAMPLES ** 2


def mix(colour, other, weight):
    """Blend two '#rrggbb' colours; weight is the share of colour."""
    a = [int(colour[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(p * weight + q * (1 - weight)):02x}" for p, q in zip(a, b))


def left_corner(row_colours, radius):
    pixels = []
    for y, colour in enumerate(row_colours):
        row = []
        for x in range(radius):
            c = coverage(x, y, radius)
            row.append(None if c < 0.5 else colour if c == 1.0 else mix(colour, EDGE, c))
        pixels.append(row)
    return pixels


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--radius", type=int, default=10)
    parser.add_argument("--xfwm-dir", type=Path,
                        default=Path(__file__).resolve().parent.parent / "PRO-dark-XFCE-4.20" / "xfwm4")
    args = parser.parse_args()
    for state, source in SOURCES.items():
        _w, _h, title = read_xpm(args.xfwm_dir / f"{source}.xpm")
        left = left_corner([row[0] for row in title], args.radius)
        for side, pixels in (("left", left), ("right", [row[::-1] for row in left])):
            name = f"top-{side}-{state}"
            write_xpm(args.xfwm_dir / f"{name}.xpm", name.replace("-", "_") + "_xpm", pixels)
            print(f"wrote {name}.xpm")


if __name__ == "__main__":
    main()

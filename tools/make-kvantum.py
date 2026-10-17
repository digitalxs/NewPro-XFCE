#!/usr/bin/env python3
"""Generate the PRO-XFCE Kvantum theme from KvArc.

KvArc (by Tsu Jan, GPL-3.0-or-later, package qt-style-kvantum-themes) is
copied, recoloured to the PRO-dark-XFCE-4.20 palette and its kvconfig tuned.
The output is deterministic, so the committed theme can be checked against a
fresh run.

Usage: tools/make-kvantum.py [--src /usr/share/Kvantum/KvArc] [--out Kvantum/PRO-XFCE]
"""
import argparse
import re
from pathlib import Path

NAME = "PRO-XFCE"

# KvArc colour → PRO colour (lowercase; 8-digit entries keep their alpha).
COLOR_MAP = {
    # accent
    "#5294e2": "#5597e1", "#4693e6": "#5597e1", "#0582ff": "#5597e1",
    "#58acff": "#6aa6e8", "#3176bf": "#4a86c9", "#4c85cb": "#4a86c9",
    # surfaces
    "#f5f6f7": "#dde2e7",  # window / dock
    "#fbfbfc": "#eef1f4",  # button / combo face
    "#fafbfb": "#e6eaee",  # tab
    "#eef2f2": "#e6eaee",  # floating tab
    "#eaedf4": "#e6eaee",  # dial
    "#f8f8f8": "#f5f7f9",  # alternate base
    "#e7e8eb": "#b6b9bf",  # menubar (Thunar menubar face)
    "#ccccce": "#b5b8be", "#d6d6d8": "#b6b9c0",  # title bar gradient
    # borders and grooves
    "#d2d2d2": "#b5b8be", "#c8c8c8": "#a9adb4", "#c9cfdb": "#a9b0bd",
    "#e1e4eb": "#c9cdd3", "#cfd6e6": "#c4cad3", "#b8babf": "#9a9ea6",
    "#e1e1e1": "#c4c8ce", "#f0f0f0": "#e6eaee",
    # dark tones
    "#474d5d": "#646772",  # tooltip / shadow tone → Thunar slate
    "#5a616e": "#646772",
    # text (kvconfig uses #000000 with alpha)
    "#000000c8": "#202020", "#000000b4": "#202020", "#00000096": "#20202096",
    "#0000007d": "#2020207d", "#00000073": "#20202073",
}

# Selection elements painted with Thunar's slate instead of the accent.
SLATE = "#646772"
SCOPED_FILL = re.compile(r"(menuitem-pressed|menubaritem-pressed|menubaritem-toggled|"
                         r"itemview-pressed|itemview-toggled)(-[a-z]+)?$")

# Rounded 9-patch frames (spec radius scale: 6px widgets). Each state is
# (face top, face bottom, border). Faces follow Thunar's path-bar buttons.
RADIUS = 6
FRAMES = {
    "button": {"normal": ("#fbfcfd", "#e8ecf2", "#a9b0bd"),
               "focused": ("#ffffff", "#f1f4f7", "#8f98a8"),
               "pressed": ("#d7dce2", "#e1e5ea", "#8f98a8"),
               "toggled": ("#5f9fe6", "#4e90dc", "#4a86c9")},
    "lineedit": {"normal": ("#ffffff", "#ffffff", "#a9b0bd"),
                 "focused": ("#ffffff", "#ffffff", "#5597e1")},
}
FRAMES["combo"] = FRAMES["button"]
PIECES = ("", "-top", "-bottom", "-left", "-right",
          "-topleft", "-topright", "-bottomleft", "-bottomright")
ORIGIN = (2000, 2000)  # free canvas area for the new pieces

KVCONFIG_OVERRIDES = {
    "%General": {
        "author": "Luis Miguel P. Freitas (based on KvArc by Tsu Jan)",
        "comment": "PRO-dark-XFCE-4.20 companion for Qt apps, based on KvArc",
        "translucent_windows": "false",
        "composite": "true",
        "respect_DE": "true",
        "menu_shadow_depth": "7",
    },
    "GeneralColors": {
        "window.color": "#dde2e7",
        "base.color": "#ffffff",
        "alt.base.color": "#f5f7f9",
        "button.color": "#eef1f4",
        "light.color": "#ffffff",
        "mid.light.color": "#e6eaee",
        "dark.color": "#9a9ea6",
        "mid.color": "#c4c8ce",
        "highlight.color": "#5597e1",
        "inactive.highlight.color": "#5597e1",
        "text.color": "#202020",
        "window.text.color": "#202020",
        "button.text.color": "#202020",
        "disabled.text.color": "#20202073",
        "tooltip.text.color": "#ffffff",
        "highlight.text.color": "#ffffff",
    },
    # 6px frames for buttons (and everything inheriting them: combos, line
    # edits, spin boxes); no expansion so the 1px border stays 1px.
    "PanelButtonCommand": {"frame.top": "6", "frame.bottom": "6", "frame.left": "6",
                           "frame.right": "6", "frame.expansion": "0"},
    # Menu bar items and menu items: white text on the slate selection.
    "MenuBarItem": {"text.press.color": "#ffffff", "text.toggle.color": "#ffffff",
                    "text.focus.color": "#ffffff"},
    "MenuItem": {"text.focus.color": "#ffffff", "text.press.color": "#ffffff",
                 "text.toggle.color": "#ffffff"},
}


def recolour(text):
    def sub(m):
        c = m.group(0).lower()
        if c in COLOR_MAP:
            return COLOR_MAP[c]
        if len(c) == 9 and c[:7] in COLOR_MAP:  # #rrggbbaa: map colour, keep alpha
            return COLOR_MAP[c[:7]] + c[7:]
        return c
    return re.sub(r"#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b", sub, text)


def scope_fills(svg):
    """Give selection elements an explicit slate fill (overrides inherited accent)."""
    def fix(m):
        tag = m.group(0)
        ident = re.search(r'\bid="([^"]+)"', tag).group(1)
        if not SCOPED_FILL.match(ident):
            return tag
        if re.search(r'\bstyle="[^"]*fill:', tag):
            return re.sub(r'(\bstyle="[^"]*fill:)[^;"]+', rf"\g<1>{SLATE}", tag)
        if 'style="' in tag:
            return tag.replace('style="', f'style="fill:{SLATE};', 1)
        return re.sub(r"(\s*/?>)$", rf' style="fill:{SLATE}"\1', tag)
    return re.sub(r'<(?:path|rect|use|g)\b[^<>]*\bid="[^"]+"[^<>]*>', fix, svg, flags=re.S)


def frame_pieces(prefix, top, bottom, border, x, y, r=RADIUS):
    """SVG for the 9 pieces of one frame state, laid out from (x, y)."""
    grad = f"{prefix}-face"
    face = f"url(#{grad})"
    s = r - 1  # inner radius / face thickness inside the 1px border
    rect = '<rect x="{}" y="{}" width="{}" height="{}" style="fill:{}"/>'.format
    arc = ('<path d="M {cx} {cy} L {x0} {y0} A {rr} {rr} 0 0 {sw} {x1} {y1} Z" '
           'style="fill:{fill}"/>').format
    out = [f'<linearGradient id="{grad}" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" style="stop-color:{top}"/>'
           f'<stop offset="1" style="stop-color:{bottom}"/></linearGradient>']
    pieces = {
        "": [rect(x, y, 10, 10, face)],
        "-top": [rect(x + 20, y, 10, 1, border), rect(x + 20, y + 1, 10, s, top)],
        "-bottom": [rect(x + 40, y, 10, s, bottom), rect(x + 40, y + s, 10, 1, border)],
        "-left": [rect(x + 60, y, 1, 10, border), rect(x + 61, y, s, 10, face)],
        "-right": [rect(x + 80, y, s, 10, face), rect(x + 80 + s, y, 1, 10, border)],
    }
    # Corners: quarter disc of the border colour with the face disc inside.
    for name, (cx, cy, sx, sy), fill in (
            ("-topleft", (r, r, -1, -1), top), ("-topright", (0, 0, 1, -1), top),
            ("-bottomleft", (r, 0, -1, 1), bottom), ("-bottomright", (0, 0, 1, 1), bottom)):
        ox = x + 100 + 20 * ("topleft topright bottomleft bottomright".split().index(name[1:]))
        cx0 = ox + (r if sx < 0 else 0)
        cy0 = y + (r if sy < 0 else 0)
        sweep = 0 if sx * sy > 0 else 1
        disc = []
        for rr, colour in ((r, border), (s, fill)):
            disc.append(arc(cx=cx0, cy=cy0, x0=cx0, y0=cy0 + sy * rr, rr=rr,
                            sw=sweep, x1=cx0 + sx * rr, y1=cy0, fill=colour))
        pieces[name] = disc
    for piece in PIECES:
        out.append(f'<g id="{prefix}{piece}">' + "".join(pieces[piece]) + "</g>")
    return "\n".join(out)


def rounded_frames(svg):
    """Rename KvArc's frame pieces (kept, unused) and append rounded ones."""
    blocks, row = [], 0
    for widget, states in FRAMES.items():
        for state, (top, bottom, border) in states.items():
            prefix = f"{widget}-{state}"
            for piece in PIECES:
                svg = svg.replace(f'id="{prefix}{piece}"', f'id="kvarc-{prefix}{piece}"', 1)
            blocks.append(frame_pieces(prefix, top, bottom, border,
                                       ORIGIN[0], ORIGIN[1] + 20 * row))
            row += 1
    group = '<g id="pro-xfce-rounded-frames">\n' + "\n".join(blocks) + "\n</g>\n"
    return svg.replace("</svg>", group + "</svg>", 1)


def apply_overrides(kvconfig):
    lines = kvconfig.splitlines()
    out, section, seen = [], None, set()

    def flush():
        for key, value in KVCONFIG_OVERRIDES.get(section, {}).items():
            if (section, key) not in seen:
                out.append(f"{key}={value}")

    for line in lines:
        header = re.match(r"\[(.+)\]\s*$", line)
        if header:
            if section is not None:
                # keep a trailing blank line after added keys
                trailing = []
                while out and out[-1] == "":
                    trailing.append(out.pop())
                flush()
                out.extend(trailing)
            section = header.group(1)
            out.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if section in KVCONFIG_OVERRIDES and key in KVCONFIG_OVERRIDES[section]:
            out.append(f"{key}={KVCONFIG_OVERRIDES[section][key]}")
            seen.add((section, key))
        elif not key.startswith("font"):
            out.append(line)
    flush()
    return "\n".join(out) + "\n"


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--src", type=Path, default=Path("/usr/share/Kvantum/KvArc"))
    parser.add_argument("--out", type=Path, default=root / "Kvantum" / NAME)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    svg = rounded_frames(scope_fills(recolour((args.src / "KvArc.svg").read_text())))
    (args.out / f"{NAME}.svg").write_text(svg)
    cfg = apply_overrides(recolour((args.src / "KvArc.kvconfig").read_text()))
    (args.out / f"{NAME}.kvconfig").write_text(cfg)
    print(f"wrote {args.out}/{NAME}.svg and {NAME}.kvconfig")


if __name__ == "__main__":
    main()

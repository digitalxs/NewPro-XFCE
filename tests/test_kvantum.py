import configparser
import filecmp
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "make-kvantum.py"
OUT = ROOT / "Kvantum" / "PRO-XFCE"
SRC = Path("/usr/share/Kvantum/KvArc")
SVG = OUT / "PRO-XFCE.svg"
CFG = OUT / "PRO-XFCE.kvconfig"


def ids(path):
    return {el.get("id") for el in ET.parse(path).getroot().iter() if el.get("id")}


def config(path):
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    cp.read(path)
    return cp


def effective(cp, section, key, depth=0):
    """Value of key in section, following Kvantum's inherits= chain."""
    if section not in cp or depth > 10:
        return None
    if key in cp[section]:
        return cp[section][key]
    parent = cp[section].get("inherits")
    return effective(cp, parent, key, depth + 1) if parent else None


@unittest.skipUnless(SRC.is_dir(), "KvArc not installed (qt-style-kvantum-themes)")
class KvantumTest(unittest.TestCase):
    def test_svg_valid_xml(self):
        ET.parse(SVG)

    def test_no_kvarc_element_lost(self):
        self.assertEqual(ids(SRC / "KvArc.svg") - ids(SVG), set())

    def test_rounded_frames(self):
        """Buttons, combos and line edits use 6px frames with a 6px arc corner."""
        root = ET.parse(SVG).getroot()
        byid = {el.get("id"): el for el in root.iter() if el.get("id")}
        for prefix in ("button-normal", "button-toggled", "combo-normal", "lineedit-focused"):
            with self.subTest(element=prefix):
                corner = byid[f"{prefix}-topleft"]
                arcs = [el.get("d", "") for el in corner.iter()]
                self.assertTrue(any("A 6 6" in d for d in arcs), arcs)
        cmd = config(CFG)["PanelButtonCommand"]
        self.assertEqual([cmd.get(f"frame.{side}") for side in ("top", "bottom", "left", "right")],
                         ["6"] * 4)

    def test_no_kvarc_accent_left(self):
        for path in (SVG, CFG):
            text = path.read_text().lower()
            for colour in ("#5294e2", "#4693e6"):
                with self.subTest(file=path.name, colour=colour):
                    self.assertNotIn(colour, text)

    def test_general_colors(self):
        gc = config(CFG)["GeneralColors"]
        expected = {"window.color": "#dde2e7", "base.color": "#ffffff",
                    "text.color": "#202020", "window.text.color": "#202020",
                    "button.text.color": "#202020", "highlight.color": "#5597e1",
                    "highlight.text.color": "#ffffff"}
        self.assertEqual({k: gc.get(k) for k in expected}, expected)

    def test_settings(self):
        general = config(CFG)["%General"]
        self.assertEqual(general.get("translucent_windows"), "false")
        self.assertEqual(general.get("respect_DE"), "true")
        self.assertEqual(general.get("composite"), "true")
        fonts = [k for s in config(CFG).sections() for k in config(CFG)[s] if k.startswith("font")]
        self.assertEqual(fonts, [])

    def test_regenerates_identically(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            subprocess.run([sys.executable, "-I", str(TOOL), "--out", str(tmp)],
                           check=True, capture_output=True)
            for name in ("PRO-XFCE.svg", "PRO-XFCE.kvconfig"):
                with self.subTest(file=name):
                    self.assertTrue(filecmp.cmp(tmp / name, OUT / name, shallow=False))
        finally:
            shutil.rmtree(tmp)

    def test_other_sections_keep_kvarc_frames(self):
        """Only button/combo/lineedit frames were redrawn at 6px; sections that
        merely inherit PanelButtonCommand (progress bars, sliders, menu bar, tab
        frames…) must keep KvArc's effective frame sizes and expansion."""
        keys = ("frame.top", "frame.bottom", "frame.left", "frame.right", "frame.expansion")
        redrawn = {"button", "combo", "lineedit"}
        ours, theirs = config(CFG), config(SRC / "KvArc.kvconfig")
        changed = []
        for section in theirs.sections():
            if section in ("%General", "GeneralColors", "Hacks"):
                continue
            if effective(ours, section, "frame.element") in redrawn:
                continue
            for key in keys:
                if effective(ours, section, key) != effective(theirs, section, key):
                    changed.append((section, key, effective(theirs, section, key),
                                    effective(ours, section, key)))
        self.assertEqual(changed, [])

    def test_licence_and_credit(self):
        self.assertIn("GNU GENERAL PUBLIC LICENSE", (ROOT / "Kvantum" / "COPYING").read_text())
        self.assertIn("Version 3", (ROOT / "Kvantum" / "COPYING").read_text())
        readme = (ROOT / "Kvantum" / "README.md").read_text()
        self.assertIn("KvArc", readme)
        self.assertIn("Tsu Jan", readme)


if __name__ == "__main__":
    unittest.main()

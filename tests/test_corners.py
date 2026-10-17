import filecmp
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XFWM = ROOT / "PRO-dark-XFCE-4.20" / "xfwm4"
TOOL = ROOT / "tools" / "make-corners.py"
STATES = ["active", "inactive", "active-shaded"]
SOURCE = {"active": "title-1-active", "inactive": "title-1-inactive",
          "active-shaded": "title-1-active-shaded"}
RADIUS = 6  # smaller radius: xfwm4 cannot anti-alias, so steps show less at 6px
HEIGHT = 26


def load_tool():
    spec = importlib.util.spec_from_file_location("make_corners", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CornersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()
        cls.tmp = Path(tempfile.mkdtemp())
        cls.dir = cls.tmp / "xfwm4"
        shutil.copytree(XFWM, cls.dir)
        cls.run_tool()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    @classmethod
    def run_tool(cls):
        subprocess.run([sys.executable, "-I", str(TOOL),
                        "--xfwm-dir", str(cls.dir)], check=True, capture_output=True)

    def corner(self, side, state):
        return self.tool.read_xpm(self.dir / f"top-{side}-{state}.xpm")

    def test_dimensions(self):
        for side in ("left", "right"):
            for state in STATES:
                with self.subTest(side=side, state=state):
                    w, h, _ = self.corner(side, state)
                    self.assertEqual((w, h), (RADIUS, HEIGHT))

    def test_outer_pixel_transparent(self):
        for state in STATES:
            with self.subTest(state=state):
                self.assertIsNone(self.corner("left", state)[2][0][0])
                self.assertIsNone(self.corner("right", state)[2][0][RADIUS - 1])

    def test_rows_below_radius_opaque(self):
        for side in ("left", "right"):
            for state in STATES:
                with self.subTest(side=side, state=state):
                    rows = self.corner(side, state)[2]
                    self.assertNotIn(None, [p for row in rows[RADIUS:] for p in row])

    def test_body_matches_title(self):
        for state in STATES:
            with self.subTest(state=state):
                title = self.tool.read_xpm(self.dir / f"{SOURCE[state]}.xpm")[2]
                rows = self.corner("left", state)[2]
                for y in range(RADIUS, HEIGHT):
                    self.assertEqual(set(rows[y]), {title[y][0]}, f"row {y}")

    def test_mirror(self):
        for state in STATES:
            with self.subTest(state=state):
                left = self.corner("left", state)[2]
                right = self.corner("right", state)[2]
                self.assertEqual(right, [row[::-1] for row in left])

    def test_idempotent(self):
        before = {p.name: p.read_bytes() for p in self.dir.glob("top-*.xpm")}
        self.run_tool()
        after = {p.name: p.read_bytes() for p in self.dir.glob("top-*.xpm")}
        self.assertEqual(before, after)

    def test_roundtrip(self):
        pixels = [["#112233", None], [None, "#aabbcc"], ["#112233", "#aabbcc"]]
        path = self.tmp / "rt.xpm"
        self.tool.write_xpm(path, "rt_xpm", pixels)
        self.assertEqual(self.tool.read_xpm(path), (2, 3, pixels))

    def test_real_theme_is_generated(self):
        """Committed corners are what the tool produces (no hand edits drift)."""
        for p in self.dir.glob("top-*.xpm"):
            with self.subTest(file=p.name):
                self.assertTrue(filecmp.cmp(p, XFWM / p.name, shallow=False))


if __name__ == "__main__":
    unittest.main()

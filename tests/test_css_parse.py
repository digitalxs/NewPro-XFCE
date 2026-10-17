import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "PRO-dark-XFCE-4.20"
GTK3 = [THEME / "gtk-3.0/gtk.css", THEME / "gtk-3.0/gtk-dark.css"]
GTK4 = [THEME / "gtk-4.0/gtk.css", THEME / "gtk-4.0/gtk-dark.css"]
GTK4_UNAVAILABLE = 77


def parse(script, path):
    return subprocess.run(
        [sys.executable, "-I", str(ROOT / "tests" / script), str(path)],
        capture_output=True, text=True, cwd=path.parent,
    )


class CssParseTest(unittest.TestCase):
    def test_gtk3_css_parses_clean(self):
        for path in GTK3:
            with self.subTest(path=path.name):
                r = parse("css_parse_gtk3.py", path)
                self.assertEqual(r.returncode, 0, r.stdout)

    def test_gtk4_css_parses_clean(self):
        if parse("css_parse_gtk4.py", GTK4[0]).returncode == GTK4_UNAVAILABLE:
            self.skipTest("GTK4 typelib missing: apt install gir1.2-gtk-4.0")
        for path in GTK4:
            with self.subTest(path=path.name):
                r = parse("css_parse_gtk4.py", path)
                self.assertEqual(r.returncode, 0, r.stdout)

    def test_braces_balanced(self):
        for path in GTK3 + GTK4:
            with self.subTest(path=path.name):
                text = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.S)
                self.assertEqual(text.count("{"), text.count("}"))


if __name__ == "__main__":
    unittest.main()

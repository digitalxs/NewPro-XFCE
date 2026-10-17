import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"


class DocsTest(unittest.TestCase):
    def test_readme_sections(self):
        text = README.read_text()
        for heading in ("## What's new in v2.3", "## Recommended setup", "## Kvantum",
                        "## Distro logo"):
            with self.subTest(heading=heading):
                self.assertIn(heading, text)

    def test_fonts_documented_not_shipped(self):
        text = README.read_text()
        self.assertIn("Segoe UI", text)
        self.assertIn("Selawik", text)
        self.assertEqual(list(ROOT.rglob("*.ttf")) + list(ROOT.rglob("*.otf")), [])

    def test_icon_recommendation_is_papirus(self):
        self.assertNotIn("**Papirus-Dark** — light icons, recommended", README.read_text())
        self.assertIn("IconTheme=Papirus`", README.read_text())

    def test_screenshots_exist(self):
        refs = re.findall(r"\]\((screenshots/[^)]+\.png)\)", README.read_text())
        self.assertGreaterEqual(len(refs), 3)
        for ref in refs:
            with self.subTest(ref=ref):
                self.assertTrue((ROOT / ref).is_file())

    def test_picom_extra(self):
        self.assertRegex((ROOT / "extras" / "picom.conf").read_text(), r"(?m)^corner-radius = 0;")  # window bottoms stay square


if __name__ == "__main__":
    unittest.main()

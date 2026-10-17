import re
import unittest
from pathlib import Path

from tests.test_radius import RULE, strip_comments

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "PRO-dark-XFCE-4.20"
GTK3 = THEME / "gtk-3.0" / "gtk.css"


def rules(text):
    """{normalised selector: [normalised body, ...]} in file order."""
    out = {}
    for m in RULE.finditer(strip_comments(text)):
        sel = ", ".join(" ".join(s.split()) for s in m.group(1).split(","))
        out.setdefault(sel.strip(), []).append(" ".join(m.group(2).split()))
    return out


def last_body(sel):
    found = rules(GTK3.read_text()).get(sel)
    if not found:
        raise AssertionError(f"rule not found: {sel}")
    return found[-1]


class PanelTest(unittest.TestCase):
    def test_panel_face(self):
        body = last_body(".xfce4-panel.background")
        for decl in ("background-image: linear-gradient(to top, #7e8185 1px, #b5b8be 1px, #b6b9c0)",
                     "background-color: #b6b9bf", "color: #202020",
                     "border-radius: 0 0 6px 6px"):
            self.assertIn(decl, body)

    def test_panel_buttons(self):
        body = last_body(".xfce4-panel.background button")
        self.assertIn("background-color: transparent", body)
        self.assertIn("border-radius: 0", body)
        hover = last_body(".xfce4-panel.background button:hover, "
                          ".xfce4-panel.background button:active, "
                          ".xfce4-panel.background button:checked")
        self.assertIn("background-color: #646772", hover)
        label = last_body(".xfce4-panel.background button:hover label, "
                          ".xfce4-panel.background button:active label, "
                          ".xfce4-panel.background button:checked label")
        self.assertIn("color: #ffffff", label)

    def test_no_dark_panel_left(self):
        for sel, bodies in rules(GTK3.read_text()).items():
            if ".xfce4-panel" in sel:
                for body in bodies:
                    with self.subTest(selector=sel[:60]):
                        self.assertNotIn("shade(#686868, 0.35)", body)
                        self.assertNotIn("#37383d", body)

    def test_index_theme(self):
        text = (THEME / "index.theme").read_text()
        self.assertRegex(text, r"(?m)^IconTheme=Papirus$")
        self.assertRegex(text, r"(?m)^CursorTheme=Bibata-Modern-Ice$")


if __name__ == "__main__":
    unittest.main()

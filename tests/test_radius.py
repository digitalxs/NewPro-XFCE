import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "PRO-dark-XFCE-4.20"
GTK3 = ["gtk-3.0/gtk.css", "gtk-3.0/gtk-dark.css"]
BASE_REV = "aeb1f58"  # v2.2, before the radius rewrite

ALLOWED = {"0", "0px", "4px", "6px", "8px", "10px"}  # 4px: menu bar item tops only
PILL = {"50%", "100%", "14px", "50px", "100px"}
SCALE_NOTE = "Radius scale: small 6px, medium 8px, window 10px"
RADIUS_DECL = re.compile(r"(border(?:-[a-z]+)*-radius)\s*:\s*([^;}]*)")
RULE = re.compile(r"([^{}]*)\{([^{}]*)\}")


def strip_comments(text):
    """Blank out /* */ comments, keeping newlines so line numbers survive."""
    return re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group()), text, flags=re.S)


def radius_decls(text):
    """Yield (line, selector, property, [tokens]) for every radius declaration."""
    text = strip_comments(text)
    for rule in RULE.finditer(text):
        selector = " ".join(rule.group(1).split())
        for decl in RADIUS_DECL.finditer(rule.group(2)):
            line = text.count("\n", 0, rule.start(2) + decl.start()) + 1
            yield line, selector, decl.group(1), decl.group(2).split()


def radius_tokens(path):
    """(line, selector, token) for every value of every border-*-radius declaration."""
    return [(line, sel, tok)
            for line, sel, _prop, toks in radius_decls(Path(path).read_text())
            for tok in toks]


def normalise(css):
    return " ".join(strip_comments(css).split())


class Gtk3RadiusTest(unittest.TestCase):
    def test_gtk3_radius_on_scale(self):
        for name in GTK3:
            with self.subTest(file=name):
                bad = [(l, s[:60], t) for l, s, t in radius_tokens(THEME / name)
                       if t not in ALLOWED | PILL]
                self.assertEqual(bad, [])

    def test_scale_documented(self):
        for name in GTK3:
            with self.subTest(file=name):
                self.assertIn(SCALE_NOTE, (THEME / name).read_text())

    def test_linked_inner_edges_square(self):
        for name in GTK3:
            with self.subTest(file=name):
                old_text = subprocess.run(
                    ["git", "show", f"{BASE_REV}:PRO-dark-XFCE-4.20/{name}"],
                    cwd=ROOT, capture_output=True, text=True, check=True).stdout
                old = [d for d in radius_decls(old_text) if len(d[3]) > 1]
                new = [d for d in radius_decls((THEME / name).read_text()) if len(d[3]) > 1]
                old_by_key = {}
                for _l, sel, prop, toks in old:
                    old_by_key.setdefault((sel, prop), []).append(toks)
                broken = []
                for _l, sel, prop, toks in new:
                    for before in old_by_key.get((sel, prop), [])[:1]:
                        for i, (b, a) in enumerate(zip(before, toks)):
                            if b in ("0", "0px") and a not in ("0", "0px"):
                                broken.append((sel[:60], prop, i, before, toks))
                    if old_by_key.get((sel, prop)):
                        old_by_key[(sel, prop)].pop(0)
                self.assertEqual(broken, [])

    def test_menu_corners_rounded_except_top_left(self):
        menu_rule = ("menu, .menu, .context-menu, .popup decoration, "
                     ".csd.popup decoration { border-radius: 0 8px 8px 8px; }")
        popup_rule = ("window.popup, window.popup.background { "
                      "background-color: transparent; background-image: none; }")
        for name in GTK3:
            with self.subTest(file=name):
                css = normalise((THEME / name).read_text())
                self.assertIn(menu_rule, css)
                self.assertIn(popup_rule, css)

    def test_menubar_item_top_rounded(self):
        rule = ("menubar > menuitem:hover, menubar > menuitem:active, "
                ".menubar > menuitem:hover, .menubar > menuitem:active "
                "{ border-radius: 4px 4px 0 0; }")
        for name in GTK3:
            with self.subTest(file=name):
                self.assertIn(rule, normalise((THEME / name).read_text()))

    def test_4px_only_on_menubar_items(self):
        for name in GTK3:
            with self.subTest(file=name):
                bad = [(l, s[:60]) for l, s, t in radius_tokens(THEME / name)
                       if t == "4px" and "menubar > menuitem" not in s]
                self.assertEqual(bad, [])

    def test_menu_rule_not_overridden_later(self):
        """No rule after the menu block sets a radius on menus or popup decorations."""
        targets = {"menu", ".menu", ".context-menu", ".popup decoration", ".csd.popup decoration"}
        for name in GTK3:
            with self.subTest(file=name):
                text = (THEME / name).read_text()
                block = text.index("border-radius: 0 8px 8px 8px;")
                later = [(l, s) for l, s, _p, _t in radius_decls(text[block + 30:])
                         if targets & {part.strip() for part in s.split(",")}]
                self.assertEqual(later, [])


class Gtk4RadiusTest(unittest.TestCase):
    TOKENS = {"--radius-small": "6px", "--radius-medium": "8px", "--radius-window": "10px"}
    VARS = {"var(--radius-small)", "var(--radius-medium)", "var(--radius-window)"}

    def test_gtk4_radius_tokens_defined(self):
        css = strip_comments((THEME / "gtk-4.0/_colors.css").read_text())
        root = re.search(r":root\s*\{([^}]*)\}", css)
        self.assertIsNotNone(root, ":root block missing")
        found = dict(re.findall(r"(--radius-[a-z]+)\s*:\s*([^;]+);", root.group(1)))
        self.assertEqual(found, self.TOKENS)

    def test_gtk4_radius_uses_tokens(self):
        bad = [(l, s[:60], t) for l, s, t in radius_tokens(THEME / "gtk-4.0/gtk.css")
               if t not in {"0", "0px"} | PILL | self.VARS]
        self.assertEqual(bad, [])

    def test_gtk4_dark_builds_on_light(self):
        """GTK4 loads gtk-dark.css INSTEAD of gtk.css, so it must import it first."""
        css = strip_comments((THEME / "gtk-4.0/gtk-dark.css").read_text()).strip()
        self.assertTrue(css.startswith('@import "gtk.css";'), css[:80])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Parse a CSS file with GTK4; print each parse error as LINE:COL MESSAGE.

Exit 0 if the file parses clean, 1 otherwise, 77 if GTK4 is unavailable.
"""
import sys

import gi

try:
    gi.require_version("Gtk", "4.0")
except ValueError:
    sys.exit(77)
from gi.repository import Gtk  # noqa: E402

errors = []
provider = Gtk.CssProvider()
provider.connect(
    "parsing-error",
    lambda _p, section, err: errors.append(
        (section.get_start_location().lines + 1,
         section.get_start_location().line_chars + 1, err.message)
    ),
)
provider.load_from_path(sys.argv[1])
for line, col, msg in errors:
    print(f"{line}:{col} {msg}")
sys.exit(1 if errors else 0)

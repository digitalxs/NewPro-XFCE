#!/usr/bin/env python3
"""Parse a CSS file with GTK3; print each parse error as LINE:COL MESSAGE.

Exit 0 if the file parses clean, 1 otherwise.
"""
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

errors = []
provider = Gtk.CssProvider()
provider.connect(
    "parsing-error",
    lambda _p, section, err: errors.append(
        (section.get_start_line() + 1, section.get_start_position() + 1, err.message)
    ),
)
try:
    provider.load_from_path(sys.argv[1])
except GLib.Error:
    pass  # every error was already delivered through parsing-error
for line, col, msg in errors:
    print(f"{line}:{col} {msg}")
sys.exit(1 if errors else 0)

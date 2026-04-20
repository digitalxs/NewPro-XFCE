# NewPro-XFCE

A professional GTK/XFCE theme for the XFCE desktop.

## Compatibility

- **XFCE**: 4.20.x
- **Debian**: 13 (Trixie)
- **GTK**: 2.0, 3.24, 4.x
- **xfwm4**: 4.20.x

## Theme components

| Directory | Description |
|-----------|-------------|
| `gtk-2.0/` | GTK2 legacy theme (requires `gtk2-engines-murrine`) |
| `gtk-3.0/` | GTK3 theme (`gtk.css` light, `gtk-dark.css` dark variant) |
| `gtk-4.0/` | GTK4 compatibility layer for GTK4 apps on XFCE |
| `xfwm4/` | Window manager decorations (XPM assets + themerc) |
| `xfce-notify-4.0/` | XFCE notification daemon theme |

## Installation

Copy the theme folder to your themes directory:

```
cp -r PRO-dark-XFCE-4.20 ~/.themes/
```

Then select it in **Settings → Appearance** (GTK theme) and **Settings → Window Manager** (xfwm4 theme).

## Dependencies

- `gtk2-engines-murrine` — required for GTK2 rendering
- `gtk2-engines-pixbuf` — required for GTK2 pixmap assets

## License

GNU General Public License v2 — see `PRO-dark-XFCE-4.20/COPYING`.

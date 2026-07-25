# NewPro-XFCE

A professional GTK/XFCE theme for the XFCE desktop.

<!-- Add preview images to screenshots/ and they'll render here. See screenshots/README.md -->
<!-- ![Desktop](screenshots/desktop.png) -->

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
| `gtk-4.0/` | GTK4 layer — `gtk.css` (light), `gtk-dark.css` (dark), `_colors.css` (shared color tokens) |
| `xfwm4/` | Window manager decorations (XPM assets + themerc) |
| `xfce-notify-4.0/` | XFCE notification daemon theme |

## Installation

Copy the theme folder to your themes directory:

```
cp -r PRO-dark-XFCE-4.20 ~/.themes/
```

Then select it in **Settings → Appearance** (GTK theme) and **Settings → Window Manager** (xfwm4 theme).

To enable the dark variant for GTK4 apps:

```
gsettings set org.gnome.desktop.interface color-scheme prefer-dark
```

## Customizing the accent color

The GTK3 theme's accent color is a single source of truth. Edit one line in
`PRO-dark-XFCE-4.20/gtk-3.0/gtk.css`:

```css
@define-color accent_bg_color #5597e1;   /* default blue */
```

Change the hex to recolor the entire theme — buttons, selections, focus rings,
sliders, progress bars, and more. Some examples:

| Variant | Hex |
|---------|-----|
| Blue (default) | `#5597e1` |
| Teal | `#16a085` |
| Purple | `#8e44ad` |
| Green | `#27ae60` |

The GTK4 layer is customizable the same way via `gtk-4.0/_colors.css`.

## Dependencies

- `gtk2-engines-murrine` — required for GTK2 rendering
- `gtk2-engines-pixbuf` — required for GTK2 pixmap assets

## License

GNU General Public License v2 — see [`LICENSE`](LICENSE).

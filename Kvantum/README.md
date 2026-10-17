# PRO-XFCE — Kvantum theme

Qt companion for **PRO-dark-XFCE-4.20**, so Qt5/Qt6 apps match the GTK theme:
the same window grey, Thunar-style menu bar, slate selection, blue accent and
6px rounded buttons, combo boxes and text fields.

## Credit and licence

Based on **KvArc** by **Tsu Jan**, from the Kvantum project
(Debian package `qt-style-kvantum-themes`). KvArc is licensed under the GNU
General Public License, version 3 or later, and so is this folder — see
[`COPYING`](COPYING). The rest of the NewPro-XFCE repository is GPL-2.0-or-later.

## Install

```
mkdir -p ~/.config/Kvantum
cp -r PRO-XFCE ~/.config/Kvantum/
kvantummanager --set PRO-XFCE
```

Then make Qt apps use Kvantum, e.g. add to `~/.profile` and log in again:

```
export QT_STYLE_OVERRIDE=kvantum
```

## Regenerate

The theme is generated from KvArc; edit colours or frames in
`tools/make-kvantum.py`, then run it from the repository root:

```
python3 tools/make-kvantum.py
```

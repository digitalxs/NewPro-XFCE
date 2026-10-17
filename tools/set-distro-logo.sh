#!/bin/sh
# Set the XFCE panel menu button (Applications Menu / Whisker Menu) to the
# logo of the installed distribution, read from /etc/os-release.
#
# Usage: tools/set-distro-logo.sh [--dry-run] [--os-release FILE]
#
# Candidates, first found wins: $LOGO (and distributor-logo-<LOGO without
# -logo>), distributor-logo-$ID, $ID-logo, known icon-theme renames
# (linuxmint → linux-mint, …), distributor-logo-<ID before the first '-'>,
# then distributor-logo-$x and $x-logo for each $x in ID_LIKE. An icon counts as
# found if an .svg or .png with that name exists in the active icon theme,
# hicolor or /usr/share/pixmaps. NEWPRO_ICON_DIRS (colon-separated) replaces
# those search roots. If nothing is found, nothing is changed.

set -u

os_release=/etc/os-release
dry_run=0
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) dry_run=1 ;;
        --os-release) [ $# -ge 2 ] || { echo "--os-release needs a file" >&2; exit 2; }
                      os_release=$2; shift ;;
        -h|--help) sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

# Read KEY from os-release without sourcing it; strip one level of quotes.
os_value() {
    sed -n "s/^$1=//p" "$os_release" | tail -n 1 | sed "s/^\"\(.*\)\"\$/\1/; s/^'\(.*\)'\$/\1/"
}

id=$(os_value ID)
logo=$(os_value LOGO)
id_like=$(os_value ID_LIKE)

if [ -n "${NEWPRO_ICON_DIRS:-}" ]; then
    roots=$NEWPRO_ICON_DIRS
else
    theme=$(xfconf-query -c xsettings -p /Net/IconThemeName 2>/dev/null || true)
    roots="$HOME/.local/share/icons/$theme:/usr/share/icons/$theme:/usr/share/icons/hicolor:/usr/share/pixmaps"
fi

icon_exists() {
    old_ifs=$IFS; IFS=:
    for root in $roots; do
        IFS=$old_ifs
        [ -d "$root" ] || continue
        if [ -n "$(find "$root" \( -name "$1.svg" -o -name "$1.png" \) -print 2>/dev/null | head -n 1)" ]; then
            return 0
        fi
    done
    IFS=$old_ifs
    return 1
}

# Icon themes (Papirus) name some logos differently from os-release.
alias_of() {
    case "$1" in
        linuxmint) echo linux-mint ;;
        pop) echo pop-os ;;
        kali) echo kali-linux ;;
    esac
}

candidates="$logo"
case "$logo" in
    *-logo) candidates="$candidates distributor-logo-${logo%-logo}" ;;
esac
if [ -n "$id" ]; then
    candidates="$candidates distributor-logo-$id $id-logo"
    alias=$(alias_of "$id")
    [ -n "$alias" ] && candidates="$candidates distributor-logo-$alias"
    [ "${id%%-*}" != "$id" ] && candidates="$candidates distributor-logo-${id%%-*}"
fi
for x in $id_like; do
    candidates="$candidates distributor-logo-$x $x-logo"
done

chosen=
for cand in $candidates; do
    if icon_exists "$cand"; then
        chosen=$cand
        break
    fi
done

if [ -z "$chosen" ]; then
    echo "no logo found for ID=${id:-?} (tried:$candidates); nothing changed"
    exit 0
fi
echo "logo: $chosen"

xfconf-query -c xfce4-panel -l -v 2>/dev/null |
    awk '$1 ~ /^\/plugins\/plugin-[0-9]+$/ && ($2 == "applicationsmenu" || $2 == "whiskermenu") { print $1 }' |
    while read -r plugin; do
        echo "set $plugin/button-icon"
        if [ "$dry_run" -eq 0 ]; then
            # -n -t string: the property only exists once the icon was changed
            xfconf-query -c xfce4-panel -p "$plugin/button-icon" -n -t string -s "$chosen" ||
                { echo "failed to set $plugin/button-icon" >&2; exit 1; }
        fi
    done

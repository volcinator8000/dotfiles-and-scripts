#!/usr/bin/env bash
# hyprlock image reload_cmd: always prints an existing PNG. Caches Spotify art per track in ~/.cache/nowplaying.
PH=~/.config/hypr/scripts/noart.png
C=~/.cache/nowplaying; mkdir -p "$C"
url=$(timeout 0.3 playerctl -p spotify metadata mpris:artUrl 2>/dev/null) || url=""
[ -z "$url" ] && { echo "$PH"; exit 0; }
f="$C/$(printf '%s' "$url" | md5sum | cut -c1-16).png"
if [ -s "$f" ]; then echo "$f"; exit 0; fi
( curl -m 3 -fsSL "$url" -o "$f.part" 2>/dev/null && mv "$f.part" "$f" ) >/dev/null 2>&1 &
echo "$PH"

#!/usr/bin/env bash
# hyprlock label: "title" or "artist" line; empty when nothing plays. Never fails.
case "$1" in
    title)  timeout 0.3 playerctl -p spotify metadata --format '{{title}}' 2>/dev/null | cut -c1-40 ;;
    artist) st=$(timeout 0.3 playerctl -p spotify status 2>/dev/null); a=$(timeout 0.3 playerctl -p spotify metadata --format '{{artist}}' 2>/dev/null | cut -c1-40)
            [ -n "$a" ] && { [ "$st" = Playing ] && echo "󰐊  $a" || echo "󰏤  $a"; } ;;
esac; exit 0

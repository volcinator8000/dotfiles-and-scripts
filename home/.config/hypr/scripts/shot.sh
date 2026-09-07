#!/usr/bin/env bash
# screenshots with a shutter sound. shot.sh region | copy | full | window
S=~/.config/keysound/keysound.sh; OUT=~/Pictures/Screenshots; mkdir -p "$OUT"; F="$OUT/$(date +%Y%m%d_%H%M%S).png"
case "${1:-region}" in
    region) g=$(slurp) || exit 0; "$S" play shutter; grim -g "$g" - | satty -f - --copy-command wl-copy -o "$F" ;;
    copy)   g=$(slurp -d) || exit 0; "$S" play shutter; grim -g "$g" - | wl-copy; notify-send -a screenshot -i camera-photo "Copied to clipboard" "region $g" ;;
    full)   "$S" play shutter; grim "$F"; wl-copy < "$F"; notify-send -a screenshot -i "$F" "Screenshot saved" "$(basename "$F") · also on the clipboard" ;;
    window) g=$(hyprctl activewindow -j | python3 -c "import json,sys; c=json.load(sys.stdin); print('%d,%d %dx%d' % (c['at'][0], c['at'][1], c['size'][0], c['size'][1]))") || exit 0
            "$S" play shutter; grim -g "$g" "$F"; wl-copy < "$F"; notify-send -a screenshot -i "$F" "Window captured" "$(basename "$F") · also on the clipboard" ;;
esac

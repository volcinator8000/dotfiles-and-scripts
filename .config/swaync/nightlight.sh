#!/bin/bash
# Night light toggle for the control center / applet. Usage: nightlight.sh [on|off|toggle|state]
# Manual override on top of the hyprsunset schedule (~/.config/hypr/hyprsunset.conf).
STATE="${XDG_RUNTIME_DIR:-/tmp}/nightlight"
TEMP=4200
case "${1:-toggle}" in
    state)  [ -f "$STATE" ] && echo true || echo false; exit 0 ;;
    on)     pgrep -x hyprsunset >/dev/null || { hyprsunset >/dev/null 2>&1 & sleep 0.4; }
            hyprctl hyprsunset temperature "$TEMP" >/dev/null && touch "$STATE" ;;
    off)    hyprctl hyprsunset identity >/dev/null; rm -f "$STATE" ;;
    toggle) if [ -f "$STATE" ]; then "$0" off; else "$0" on; fi; exit 0 ;;
esac

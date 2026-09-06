#!/bin/bash
# Keep-awake inhibitor for the control center. Usage: keepawake.sh [on|off|toggle|state]
running() { pgrep -f "systemd-inhibit.*SwayNC" >/dev/null; }
case "${1:-toggle}" in
    state)  running && echo true || echo false; exit 0 ;;
    on)     running || systemd-inhibit --what=idle --who="SwayNC" --why="User requested Keep Awake" sleep infinity >/dev/null 2>&1 & ;;
    off)    pkill -f "systemd-inhibit.*SwayNC" ;;
    toggle) if running; then "$0" off; else "$0" on; fi; exit 0 ;;
esac
sleep 0.3; pkill -RTMIN+8 waybar

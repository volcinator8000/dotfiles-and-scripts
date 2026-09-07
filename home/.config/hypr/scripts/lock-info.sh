#!/usr/bin/env bash
# hyprlock labels; every branch must return fast and never fail
case "$1" in
    away)  AT="${XDG_RUNTIME_DIR:-/tmp}/locked-at"; [ -f "$AT" ] || exit 0; s=$(( $(date +%s) - $(cat "$AT") ))
           if (( s < 60 )); then echo "AWAY  <1 MIN"; elif (( s < 3600 )); then echo "AWAY  $((s / 60)) MIN"; else printf 'AWAY  %dH %02dM\n' $((s / 3600)) $((s % 3600 / 60)); fi ;;
    net)   ssid=$(timeout 0.4 nmcli -t -f NAME,TYPE con show --active 2>/dev/null | awk -F: '$2 ~ /wireless/ {print $1; exit}')
           if [ -n "$ssid" ]; then echo "󰖩  $ssid"; elif [ "$(timeout 0.3 nmcli radio wifi 2>/dev/null)" = enabled ]; then echo "󰖪  no network"; else echo "󰖪  wifi off"; fi ;;
    batt)  timeout 0.6 ~/.config/waybar/scripts/battery.sh --text 2>/dev/null ;;
esac; exit 0

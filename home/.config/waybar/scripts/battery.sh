#!/usr/bin/env bash
# custom/battery: icon + percent, tooltip with upower's time estimates (minute precision)
dev=$(upower -e | grep -m1 BAT) || { echo '{"text":"","class":"none"}'; exit 0; }
eval "$(upower -i "$dev" | awk -F': *' '
  /state:/            {print "state="$2}
  /energy:/           {print "e="$2+0}
  /energy-full:/      {print "ef="$2+0}
  /energy-full-design:/{print "efd="$2+0}
  /energy-rate:/      {print "rate="$2+0}
  /percentage:/       {gsub("%","",$2); print "pct="$2+0}
  /capacity:/         {gsub("%","",$2); print "health="$2+0}
  /charge-cycles:/    {print "cycles=\""$2"\""}')"
icons=(󰂎 󰁺 󰁻 󰁼 󰁽 󰁾 󰁿 󰂀 󰂁 󰂂 󰁹)
idx=$(( pct / 10 )); (( idx > 10 )) && idx=10
hm() { local m=$1; printf '%dh %02dmin' $((m / 60)) $((m % 60)); }
class=$state; icon=${icons[$idx]}; line=""
case "$state" in
    discharging)
        if awk "BEGIN{exit !($rate > 0.5)}"; then line="$(hm "$(awk "BEGIN{printf \"%d\", $e / $rate * 60}")") until empty"; else line="estimating…"; fi
        (( pct <= 15 )) && class=critical || { (( pct <= 30 )) && class=warning; } ;;
    charging)
        icon=󰂄
        if awk "BEGIN{exit !($rate > 0.5)}"; then line="$(hm "$(awk "BEGIN{printf \"%d\", ($ef - $e) / $rate * 60}")") until full"; else line="estimating…"; fi ;;
    fully-charged) icon=󰁹; class=full; line="fully charged" ;;
    pending-charge|pending-discharge) icon=󰚥; class=plugged; line="plugged, not charging" ;;
esac
# ── sound events on state changes (plug / unplug / battery low), state kept in the runtime dir ──
ST="${XDG_RUNTIME_DIR:-/tmp}/battery-state"; prev=$(cat "$ST" 2>/dev/null); KS=~/.config/keysound/keysound.sh
PA=~/.config/hypr/power-auto.conf; pa() { sed -n "s/^$1=//p" "$PA" 2>/dev/null; }
eco() {  # eco on|off : compositor eye-candy costs iGPU power; brightness cap on unplug
    if [ "$(pa eco_effects)" = true ]; then
        if [ "$1" = on ]; then hyprctl --batch "keyword decoration:blur:enabled false; keyword decoration:shadow:enabled false" >/dev/null 2>&1
        else hyprctl reload >/dev/null 2>&1; fi   # reload restores whatever hyprland.lua says
    fi
    lvl=$(pa eco_brightness); [ "$1" = on ] && [ "${lvl:-0}" -gt 0 ] 2>/dev/null && { cur=$(brightnessctl -m | cut -d, -f4 | tr -d %); [ "$cur" -gt "$lvl" ] && brightnessctl -q set "$lvl%"; }
}
if [ -n "$prev" ] && [ "$prev" != "$state" ]; then
    case "$state" in
        charging|fully-charged|pending-charge)
            [ "$prev" = discharging ] && { "$KS" play plug
                if [ "$(pa enabled)" = true ] && [ -n "$(pa on_ac)" ]; then powerprofilesctl set "$(pa on_ac)" 2>/dev/null && notify-send -a power -i battery-good-charging "Charger connected" "profile: $(pa on_ac)"; fi
                eco off; } ;;
        discharging)
            "$KS" play unplug
            if [ "$(pa enabled)" = true ] && [ -n "$(pa on_battery)" ]; then powerprofilesctl set "$(pa on_battery)" 2>/dev/null && notify-send -a power -i battery-good "On battery" "profile: $(pa on_battery)"; fi
            eco on ;;
    esac
fi
echo "$state" > "$ST"
LOW="${XDG_RUNTIME_DIR:-/tmp}/battery-low-warned"
if [ "$state" = discharging ] && (( pct <= 15 )); then
    [ -f "$LOW" ] || { "$KS" play batt-low; notify-send -u critical -a battery -i battery-caution "Battery ${pct}%" "$line"; touch "$LOW"; }
else rm -f "$LOW"; fi
if [ "$1" = "--text" ]; then  # plain line for hyprlock
    case "$state" in charging) echo "󰂄 ${pct}%  ${line}" ;; fully-charged) echo "󰁹 ${pct}%  full" ;; *) echo "${icon} ${pct}%  ${line}" ;; esac; exit 0
fi
tip="$line\n$(printf '%.1f' "$rate") W · ${pct}% of $(printf '%.1f' "$ef") Wh\nhealth ${health}% (design $(printf '%.1f' "$efd") Wh)"
[ -n "$cycles" ] && [ "$cycles" != "N/A" ] && tip+=" · $cycles cycles"
printf '{"text":"%s %s%%","tooltip":"%s","class":"%s","percentage":%s}\n' "$icon" "$pct" "$tip" "$class" "$pct"

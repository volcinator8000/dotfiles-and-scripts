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
tip="$line\n$(printf '%.1f' "$rate") W · ${pct}% of $(printf '%.1f' "$ef") Wh\nhealth ${health}% (design $(printf '%.1f' "$efd") Wh)"
[ -n "$cycles" ] && [ "$cycles" != "N/A" ] && tip+=" · $cycles cycles"
printf '{"text":"%s %s%%","tooltip":"%s","class":"%s","percentage":%s}\n' "$icon" "$pct" "$tip" "$class" "$pct"

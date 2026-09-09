#!/usr/bin/env bash
# custom/stats: cpu · mem · gpu · disk · temp as one module (pango-coloured), detailed tooltip.
RT="${XDG_RUNTIME_DIR:-/tmp}"
# persistent: one JSON line every 3 s (no re-spawning bash + python each tick)
while :; do
    # cpu: delta of /proc/stat since last run
    read -r _ u n s i w q sq st _ < /proc/stat; total=$((u+n+s+i+w+q+sq+st)); idle=$((i+w))
    if [[ -f "$RT/stats-cpu" ]]; then read -r pt pi < "$RT/stats-cpu"; dt=$((total-pt)); di=$((idle-pi)); cpu=$(( dt > 0 ? (dt-di)*100/dt : 0 )); else cpu=0; fi
    echo "$total $idle" > "$RT/stats-cpu"; read -r l1 l5 l15 _ < /proc/loadavg
    # memory
    mt=$(awk '/MemTotal/{print $2}' /proc/meminfo); ma=$(awk '/MemAvailable/{print $2}' /proc/meminfo); mem=$(( (mt-ma)*100/mt ))
    memg=$(awk -v u=$((mt-ma)) -v t=$mt 'BEGIN{printf "%.1f / %.1f GiB", u/1048576, t/1048576}')
    # disk
    read -r dsize dused dfree dpct < <(df -h --output=size,used,avail,pcent / | tail -1); dpct=${dpct%\%}
    # temp: k10temp (cpu die) if present, else thermal zone 0
    tp=""; for h in /sys/class/hwmon/hwmon*; do [[ "$(cat "$h/name" 2>/dev/null)" == k10temp ]] && tp="$h/temp1_input" && break; done
    [[ -z "$tp" ]] && tp=/sys/class/thermal/thermal_zone0/temp; temp=$(( $(cat "$tp" 2>/dev/null || echo 0) / 1000 ))
    ticon=$(printf '\U000F050F'); (( temp >= 85 )) && ticon=$(printf '\U000F0E01')
    tcol="#ff5a1f"; (( temp >= 85 )) && tcol="#ff2d3a"
    # gpu: reuse gpu.sh (runtime-PM safe); its text is the icon, tooltip has the detail
    gj=$(~/.config/waybar/scripts/gpu.sh 2>/dev/null)
    gtxt=$(printf '%s' "$gj" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('text',''))" 2>/dev/null)
    gtip=$(printf '%s' "$gj" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tooltip','').replace(chr(10), chr(92)+'n'))" 2>/dev/null)
    gcls=$(printf '%s' "$gj" | python3 -c "import json,sys; print(json.load(sys.stdin).get('class',''))" 2>/dev/null)
    gcol="#39ff14"; [[ "$gcls" == *dgpu* ]] && gcol="#ff5cc8"; [[ "$gcls" == *critical* ]] && gcol="#ff2d3a"
    ccol="#3ae0ff"; (( cpu >= 85 )) && ccol="#ffb000"; mcol="#a64dff"; (( mem >= 90 )) && mcol="#ffb000"
    esc() { printf '%s' "$1" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g'; }
    # fixed-width numbers (monospace bar font): every value padded to 3 columns so 7% and 100% take the same space
    gicon="${gtxt%% *}"; gnum="${gtxt##* }"; gnum="${gnum%\%}"; [[ "$gnum" =~ ^[0-9]+$ ]] || gnum=""
    gcell="$(esc "$gicon") $(printf '%3s' "$gnum")%"; [[ -z "$gnum" ]] && gcell="$(esc "$gicon")     "
    text="<span color='$ccol'>󰻠 $(printf '%3d' "$cpu")%</span>  <span color='$mcol'>󰍛 $(printf '%3d' "$mem")%</span>  <span color='$gcol'>$gcell</span>  <span color='#ff5cc8'>󰋊 $(printf '%3d' "$dpct")%</span>  <span color='$tcol'>$ticon $(printf '%3d' "$temp")°</span>"
    tip="cpu ${cpu}%  ·  load $l1 $l5 $l15\nmemory $memg\n$(esc "$gtip")\ndisk $dused used · $dfree free of $dsize\ncpu temp ${temp}°C"
    cls="ok"; (( temp >= 85 || cpu >= 95 )) && cls="critical"
    printf '{"text":"%s","tooltip":"%s","class":"%s"}\n' "$text" "$tip" "$cls"
    sleep 3
done

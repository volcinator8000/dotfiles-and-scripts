#!/usr/bin/env bash
# Waybar module: iGPU load + dGPU power state.
# Never touch busy/temp/power of a runtime-suspended card: those sysfs reads wake it
# and reset its autosuspend timer, which is exactly what keeps the dGPU from sleeping.
IGPU=0000:08:00.0; DGPU=0000:03:00.0
tip=""; cls="ok"
card_of() { ls -d /sys/bus/pci/devices/$1/drm/card[0-9]* 2>/dev/null | head -1; }

# iGPU: always active (drives the panel), safe to read
ic=$(card_of $IGPU)
ibusy=$(cat "$ic/device/gpu_busy_percent" 2>/dev/null || echo 0)
itemp=$(cat "$ic"/device/hwmon/hwmon*/temp1_input 2>/dev/null | head -1); itemp=$(( ${itemp:-0} / 1000 ))
tip+="iGPU 680M   ${ibusy}%  ${itemp}°C\n"
[[ $itemp -ge 85 ]] && cls="critical"

# dGPU: runtime_status is a plain PM attribute and does not wake the device
dc=$(card_of $DGPU)
dstate=$(cat "$dc/device/power/runtime_status" 2>/dev/null || echo unknown)
if [[ "$dstate" == "active" ]]; then
    # only read details while it is awake anyway; skip 9 of 10 ticks so a card that just
    # went idle gets a chance to autosuspend instead of being re-polled every 3 s
    stamp=/tmp/waybar-gpu-tick; n=$(( ($(cat $stamp 2>/dev/null || echo 0) + 1) % 10 )); echo $n > $stamp
    cache=/tmp/waybar-gpu-dgpu
    if [[ $n -eq 0 || ! -f $cache ]]; then
        dbusy=$(cat "$dc/device/gpu_busy_percent" 2>/dev/null || echo 0)
        dtemp=$(cat "$dc"/device/hwmon/hwmon*/temp1_input 2>/dev/null | head -1); dtemp=$(( ${dtemp:-0} / 1000 ))
        dpw=$(cat "$dc"/device/hwmon/hwmon*/power1_average 2>/dev/null | head -1); dpw=$(awk -v p="${dpw:-0}" 'BEGIN{printf "%.1f", p/1000000}')
        echo "$dbusy $dtemp $dpw" > $cache
    fi
    read -r dbusy dtemp dpw < $cache
    tip+="dGPU 6500M  ${dbusy}%  ${dtemp}°C  ${dpw}W  [awake]"
    dicon="󰢮"; [[ ${dbusy:-0} -gt 0 ]] && cls="dgpu"
else
    tip+="dGPU 6500M  [$dstate]"
    dicon="󰢯"
fi
printf '{"text":"%s %s%%","tooltip":"%s","class":"%s"}\n' "$dicon" "$ibusy" "$tip" "$cls"

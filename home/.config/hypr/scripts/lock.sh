#!/usr/bin/env bash
# lock wrapper: remembers when the lock started (for the "away" label) and plays lock/unlock sounds.
# A *live* hyprlock is never killed (a dead session lock needs a reboot). But hyprlock 0.9.6 sometimes hangs at
# startup before ever locking (all threads parked in futex_wait, zero CPU) and that ghost blocks every later lock
# through the "already running" check. Such a ghost is detected by three consecutive idle samples and removed.
KS=~/.config/keysound/keysound.sh; RT="${XDG_RUNTIME_DIR:-/tmp}"; AT="$RT/locked-at"
P=$(pgrep -x hyprlock | head -1)
if [ -n "$P" ]; then
    idle=0
    for _ in 1 2 3; do
        a=$(awk '{print $14+$15}' /proc/$P/stat 2>/dev/null) || break; w=$(cat /proc/$P/wchan 2>/dev/null); sleep 1
        b=$(awk '{print $14+$15}' /proc/$P/stat 2>/dev/null) || break
        [[ "$w" == futex_wait* && "$b" == "$a" ]] && idle=$((idle + 1))
    done
    if (( idle == 3 )); then
        echo "$(date '+%F %T') killed ghost hyprlock $P (futex_wait, no cpu, no frames)" >> "$RT/lock-wrapper.log"
        kill "$P"; sleep 0.5
    else
        exit 0   # a real lock screen is up
    fi
fi
date +%s > "$AT"
"$KS" play lock
hyprlock
"$KS" play unlock
rm -f "$AT"

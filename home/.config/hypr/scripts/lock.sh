#!/usr/bin/env bash
# lock wrapper: remembers when the lock started (for the "away" label) and plays lock/unlock sounds.
# A *live* hyprlock is never killed (a dead session lock needs a reboot). But hyprlock 0.9.6 sometimes hangs at
# startup before ever locking (all threads parked in futex_wait, zero CPU) and that ghost blocks every later lock
# through the "already running" check. Such a ghost is detected by three consecutive idle samples and removed.
KS=~/.config/keysound/keysound.sh; RT="${XDG_RUNTIME_DIR:-/tmp}"; AT="$RT/locked-at"
P=$(pgrep -x hyprlock | head -1)
if [ -n "$P" ]; then
    # ghost = zero CPU AND zero bytes read over 4 s. A live lock screen re-renders its clock every second
    # (CPU ticks) and keeps reading its Wayland socket and label pipes (rchar grows). Both flat = hung.
    a=$(awk '{print $14+$15}' /proc/$P/stat 2>/dev/null); ra=$(awk '/^rchar/{print $2}' /proc/$P/io 2>/dev/null)
    sleep 4
    b=$(awk '{print $14+$15}' /proc/$P/stat 2>/dev/null); rb=$(awk '/^rchar/{print $2}' /proc/$P/io 2>/dev/null)
    if [ -n "$a" ] && [ -n "$b" ] && [ "$a" = "$b" ] && [ -n "$ra" ] && [ "$ra" = "$rb" ]; then
        echo "$(date '+%F %T') killed ghost hyprlock $P (no cpu, no io for 4 s)" >> "$RT/lock-wrapper.log"
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

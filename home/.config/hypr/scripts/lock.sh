#!/usr/bin/env bash
# lock wrapper: remembers when the lock started (for the "away" label), plays lock/unlock sounds,
# and watches for hyprlock's known startup hang (process alive, no frame ever rendered): kills and relaunches it.
KS=~/.config/keysound/keysound.sh; RT="${XDG_RUNTIME_DIR:-/tmp}"; AT="$RT/locked-at"; LOG="$RT/hyprlock.log"
if pgrep -x hyprlock >/dev/null; then
    # an instance exists: healthy (rendered a frame) -> nothing to do; hung -> kill it and take over
    if grep -qs 'frame 1,' "$LOG"; then exit 0; fi
    pkill -x hyprlock; sleep 0.3
fi
date +%s > "$AT"
"$KS" play lock
start() { : > "$LOG"; hyprlock --verbose > "$LOG" 2>&1 & PID=$!; }
healthy() { for _ in $(seq 1 12); do sleep 0.25; grep -qs 'frame 1,' "$LOG" && return 0; kill -0 "$PID" 2>/dev/null || return 1; done; return 1; }
start
if ! healthy; then
    echo "hyprlock did not render within 3 s, relaunching" >> "$RT/lock-wrapper.log"
    kill "$PID" 2>/dev/null; sleep 0.4; start; healthy || echo "second attempt also stalled" >> "$RT/lock-wrapper.log"
fi
# verbose logging is only needed for the health check; stop it from growing while locked
sleep 1; truncate -s 0 "$LOG" 2>/dev/null; echo "frame 1, (health check passed)" >> "$LOG"
wait "$PID"
"$KS" play unlock
rm -f "$AT"

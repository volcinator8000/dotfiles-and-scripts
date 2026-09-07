#!/usr/bin/env bash
# lock wrapper: remembers when the lock started (for the "away" label) and plays lock/unlock sounds.
# NEVER kills hyprlock: killing a live session-lock client leaves Hyprland in a dead lock that only a reboot clears.
KS=~/.config/keysound/keysound.sh; AT="${XDG_RUNTIME_DIR:-/tmp}/locked-at"
pgrep -x hyprlock >/dev/null && exit 0
date +%s > "$AT"
"$KS" play lock
hyprlock
"$KS" play unlock
rm -f "$AT"

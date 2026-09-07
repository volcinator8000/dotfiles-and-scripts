#!/usr/bin/env bash
# lock wrapper: remembers when the lock started (for the "away" label), plays lock/unlock sounds.
KS=~/.config/keysound/keysound.sh; AT="${XDG_RUNTIME_DIR:-/tmp}/locked-at"
pgrep -x hyprlock >/dev/null && exit 0
date +%s > "$AT"
"$KS" play lock
hyprlock
"$KS" play unlock
rm -f "$AT"

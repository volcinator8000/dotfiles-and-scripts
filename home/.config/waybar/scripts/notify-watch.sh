#!/usr/bin/env bash
# waybar custom/notification exec: relays swaync's subscription and plays the theme sound when the
# notification count goes UP (not on dismiss). Replaces swaync's `scripts` hook, which was crashing it.
KS=~/.config/keysound/keysound.sh; prev=-1
swaync-client -swb | while IFS= read -r line; do
    printf '%s\n' "$line"
    n=$(printf '%s' "$line" | sed -n 's/.*"count": *\([0-9]*\).*/\1/p'); cls=$(printf '%s' "$line" | sed -n 's/.*"class": *"\([^"]*\)".*/\1/p')
    if [[ "$n" =~ ^[0-9]+$ ]]; then
        if (( prev >= 0 && n > prev )) && [[ "$cls" != dnd* ]] && [[ "$cls" != inhibited* ]]; then "$KS" play notify & fi
        prev=$n
    fi
done

#!/usr/bin/env bash
# Click action for the waybar updates module: open a wide kitty window with a banner,
# the pending list, then run the upgrade. `--dry` only shows the banner + list.
DRY=""; [[ "$1" == "--dry" ]] && DRY=1
if [[ -z "$INSIDE_UPDATE_WINDOW" ]]; then
    INSIDE_UPDATE_WINDOW=1 exec kitty --title "system-update" \
        -o initial_window_width=132c -o initial_window_height=40c \
        -o font_size=11 -o background_opacity=0.94 \
        -e "$0" "$@"
fi

# cybersigilism palette (24-bit)
B=$'\e[38;2;58;224;255m'; P=$'\e[38;2;166;77;255m'; K=$'\e[38;2;255;92;200m'
A=$'\e[38;2;255;176;0m'; G=$'\e[38;2;57;255;20m'; R=$'\e[38;2;255;45;58m'
M=$'\e[38;2;107;107;120m'; T=$'\e[38;2;220;220;227m'; X=$'\e[0m'

banner=(
'███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗    ██╗   ██╗██████╗ ██████╗  █████╗ ████████╗███████╗'
'██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████║    ██║   ██║██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔════╝'
'███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║    ██║   ██║██████╔╝██║  ██║███████║   ██║   █████╗  '
'╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║    ██║   ██║██╔═══╝ ██║  ██║██╔══██║   ██║   ██╔══╝  '
'███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║    ╚██████╔╝██║     ██████╔╝██║  ██║   ██║   ███████╗'
'╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝     ╚═════╝ ╚═╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝'
)
colors=("$B" "$B" "$P" "$P" "$K" "$K")
clear; echo
for i in "${!banner[@]}"; do printf '  %s%s%s\n' "${colors[$i]}" "${banner[$i]}" "$X"; done
printf '  %s%s%s\n' "$M" "$(printf '─%.0s' $(seq 1 108))" "$X"
printf '  %s%-40s%s%s%s\n' "$M" "$(date '+%a %d %b %Y  %H:%M' | tr a-z A-Z)" "$B" "$(echo "${HOSTNAME:-$(uname -n)} // $USER" | tr a-z A-Z)" "$X"
echo

# pending list from the checker's cache (fast) — refresh if older than 30 min
cache="${XDG_RUNTIME_DIR:-/tmp}/waybar-updates.json"
if [[ ! -f "$cache" || $(( $(date +%s) - $(stat -c %Y "$cache") )) -gt 1800 ]]; then
    printf '  %s…checking for updates%s\n\n' "$M" "$X"; "$HOME/.config/waybar/scripts/updates.sh" >/dev/null 2>&1
fi
python3 - "$cache" "$B" "$A" "$M" "$X" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    d = {"tooltip": "no cache"}
B, A, M, X = sys.argv[2:6]
lines = d.get("tooltip", "").split("\n")
print(f"  {A}{lines[0]}{X}")
for l in lines[2:]:
    if not l.strip(): continue
    if " -> " in l:
        name, rest = l.split(" ", 1)
        old, new = rest.split(" -> ")
        print(f"  {B}▸{X} {name:<34} {M}{old:>22}{X}  →  {A}{new}{X}")
    else:
        print(f"  {M}{l}{X}")
PY
echo
if [[ -n "$DRY" ]]; then printf '  %s[dry run] press Enter to close%s ' "$M" "$X"; read -r _; exit 0; fi

printf '  %s%s%s\n\n' "$M" "$(printf '─%.0s' $(seq 1 108))" "$X"
paru -Syu
rc=$?
echo
if [[ $rc -eq 0 ]]; then printf '  %s✔ done%s' "$G" "$X"; else printf '  %s✘ paru exited with %s%s' "$R" "$rc" "$X"; fi
printf '  %s— press Enter to close%s ' "$M" "$X"; read -r _
pkill -RTMIN+9 waybar

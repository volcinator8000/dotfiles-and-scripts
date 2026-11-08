#!/usr/bin/env bash
# keysound control: start | stop | toggle | state | mute | volume <0-1> | pack [name] | packs | restart | test
#                   play <event> | system on|off|state | system-volume <0-1>   (system sounds: notify notify-urgent lock unlock shutter plug unplug batt-low)
D=~/.config/keysound
case "${1:-start}" in
    start)  systemctl --user start keysound 2>/dev/null || { pgrep -f '^(/usr/bin/)?python3 .*keysoundd.py' >/dev/null || setsid -f python3 "$D/keysoundd.py" </dev/null >>"${XDG_RUNTIME_DIR:-/tmp}/keysound.log" 2>&1; } ;;   # systemd unit restarts it if it crashes
    stop)   systemctl --user stop keysound 2>/dev/null; pkill -f '^(/usr/bin/)?python3 .*keysoundd.py' ;;
    toggle) if pgrep -f '^(/usr/bin/)?python3 .*keysoundd.py' >/dev/null; then "$0" stop; else "$0" start; fi ;;
    state)  pgrep -f '^(/usr/bin/)?python3 .*keysoundd.py' >/dev/null && echo true || echo false ;;
    mute)   pkill -USR1 -f '^(/usr/bin/)?python3 .*keysoundd.py' ;;
    volume) sed -i "s/^volume=.*/volume=$2/" "$D/config"; pkill -HUP -f '^(/usr/bin/)?python3 .*keysoundd.py' ;;
    restart) systemctl --user restart keysound 2>/dev/null && exit 0; pkill -f '^(/usr/bin/)?python3 .*keysoundd.py'; for i in $(seq 1 20); do pgrep -f '^(/usr/bin/)?python3 .*keysoundd.py' >/dev/null || break; sleep 0.1; done
             setsid -f python3 "$D/keysoundd.py" </dev/null >>"${XDG_RUNTIME_DIR:-/tmp}/keysound.log" 2>&1 ;;
    pack)   if [ -n "$2" ]; then sed -i "s/^pack=.*/pack=$2/" "$D/config"; pkill -HUP -f '^(/usr/bin/)?python3 .*keysoundd.py'; else sed -n 's/^pack=//p' "$D/config"; fi ;;
    packs)  ls -1 "$D/packs" ;;
    play)   # system sound from the active pack; honours system=, system_volume= and swaync do-not-disturb
            [ "$(sed -n 's/^system=//p' "$D/config")" = "false" ] && exit 0
            # do-not-disturb: ask whichever notification daemon is actually running, never block.
            # (swaync-client waits forever when swaync is down, holding a D-Bus connection; enough
            # of those exhausted the session bus on 2026-11-08 and took every app down with it.)
            if [ "$3" != "--force" ] && [ "$2" != "lock" ] && [ "$2" != "unlock" ]; then
                if pgrep -x swaync >/dev/null; then dnd=$(timeout 1 swaync-client -D 2>/dev/null)
                elif pgrep -x qs >/dev/null; then dnd=$(timeout 1 qs -c sigil ipc call notifs isDnd 2>/dev/null)
                fi
                [ "$dnd" = "true" ] && exit 0
            fi
            p=$(sed -n 's/^pack=//p' "$D/config"); v=$(sed -n 's/^system_volume=//p' "$D/config")
            f="$D/packs/${p:-cybersigil}/$2.wav"; [ -f "$f" ] || f="$D/packs/cybersigil/$2.wav"
            [ -f "$f" ] && setsid -f pw-play --volume "${v:-0.6}" "$f" </dev/null >/dev/null 2>&1 ;;
    system) case "$2" in
                on|off) sed -i "s/^system=.*/system=$([ "$2" = on ] && echo true || echo false)/" "$D/config" ;;
                *) [ "$(sed -n 's/^system=//p' "$D/config")" = "false" ] && echo false || echo true ;;
            esac ;;
    system-volume) sed -i "s/^system_volume=.*/system_volume=$2/" "$D/config" ;;
    test)   p=$(sed -n 's/^pack=//p' "$D/config"); for s in key0 key1 key2 space key3 backspace enter hold release; do pw-play --volume 0.6 "$D/packs/${p:-cybersigil}/$s.wav"; sleep 0.08; done ;;
esac

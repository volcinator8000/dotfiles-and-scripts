#!/usr/bin/env bash
# keysound control: start | stop | toggle | state | mute | volume <0-1> | pack [name] | packs | restart | test
#                   play <event> | system on|off|state | system-volume <0-1>   (system sounds: notify notify-urgent lock unlock shutter plug unplug batt-low)
D=~/.config/keysound
case "${1:-start}" in
    start)  pgrep -f '^python3 .*keysoundd.py' >/dev/null || python3 "$D/keysoundd.py" >>"${XDG_RUNTIME_DIR:-/tmp}/keysound.log" 2>&1 & ;;
    stop)   pkill -f '^python3 .*keysoundd.py' ;;
    toggle) if pgrep -f '^python3 .*keysoundd.py' >/dev/null; then pkill -f '^python3 .*keysoundd.py'; else python3 "$D/keysoundd.py" >>"${XDG_RUNTIME_DIR:-/tmp}/keysound.log" 2>&1 & fi ;;
    state)  pgrep -f '^python3 .*keysoundd.py' >/dev/null && echo true || echo false ;;
    mute)   pkill -USR1 -f '^python3 .*keysoundd.py' ;;
    volume) sed -i "s/^volume=.*/volume=$2/" "$D/config"; pkill -HUP -f '^python3 .*keysoundd.py' ;;
    restart) pkill -f '^python3 .*keysoundd.py'; for i in $(seq 1 20); do pgrep -f '^python3 .*keysoundd.py' >/dev/null || break; sleep 0.1; done
             python3 "$D/keysoundd.py" >>"${XDG_RUNTIME_DIR:-/tmp}/keysound.log" 2>&1 & ;;
    pack)   if [ -n "$2" ]; then sed -i "s/^pack=.*/pack=$2/" "$D/config"; pkill -HUP -f '^python3 .*keysoundd.py'; else sed -n 's/^pack=//p' "$D/config"; fi ;;
    packs)  ls -1 "$D/packs" ;;
    play)   # system sound from the active pack; honours system=, system_volume= and swaync do-not-disturb
            [ "$(sed -n 's/^system=//p' "$D/config")" = "false" ] && exit 0
            [ "$3" != "--force" ] && [ "$(swaync-client -D 2>/dev/null)" = "true" ] && [ "$2" != "lock" ] && [ "$2" != "unlock" ] && exit 0
            p=$(sed -n 's/^pack=//p' "$D/config"); v=$(sed -n 's/^system_volume=//p' "$D/config")
            f="$D/packs/${p:-cybersigil}/$2.wav"; [ -f "$f" ] || f="$D/packs/cybersigil/$2.wav"
            [ -f "$f" ] && pw-play --volume "${v:-0.6}" "$f" >/dev/null 2>&1 & ;;
    system) case "$2" in
                on|off) sed -i "s/^system=.*/system=$([ "$2" = on ] && echo true || echo false)/" "$D/config" ;;
                *) [ "$(sed -n 's/^system=//p' "$D/config")" = "false" ] && echo false || echo true ;;
            esac ;;
    system-volume) sed -i "s/^system_volume=.*/system_volume=$2/" "$D/config" ;;
    test)   p=$(sed -n 's/^pack=//p' "$D/config"); for s in key0 key1 key2 space key3 backspace enter hold release; do pw-play --volume 0.6 "$D/packs/${p:-cybersigil}/$s.wav"; sleep 0.08; done ;;
esac

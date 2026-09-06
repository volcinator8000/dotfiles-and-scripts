#!/usr/bin/env bash
# keysound control: start | stop | toggle | state | mute | volume <0-1> | pack [name] | packs | restart | test
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
    test)   p=$(sed -n 's/^pack=//p' "$D/config"); for s in key0 key1 key2 space key3 backspace enter hold release; do pw-play --volume 0.6 "$D/packs/${p:-cybersigil}/$s.wav"; sleep 0.08; done ;;
esac

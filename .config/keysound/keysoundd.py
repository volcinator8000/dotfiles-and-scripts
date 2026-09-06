#!/usr/bin/env python3
"""Typewriter-style key sounds for Wayland: reads keyboard evdev nodes directly and
streams a mixed audio signal to pacat (pipewire-pulse) with ~15 ms latency.
Controls: SIGUSR1 = mute/unmute, SIGHUP = reload config (~/.config/keysound/config)."""
import glob, os, random, select, signal, struct, subprocess, sys, threading, time, wave

HOME = os.path.expanduser("~/.config/keysound")
PACKS = os.path.join(HOME, "packs")
CFG = os.path.join(HOME, "config")
SR, CHUNK = 44100, 441           # 10 ms chunks
EV_KEY, EVSZ = 1, struct.calcsize("llHHi")
KEY_ENTER, KEY_KPENTER, KEY_SPACE, KEY_BACKSPACE = 28, 96, 57, 14
MODS = {42, 54, 29, 97, 56, 100, 58, 15}   # shifts, ctrls, alts, caps, tab
SUPER = {125, 126}                          # special case: sweep on press, blip on release

cfg = {"volume": 0.6, "enabled": True, "pack": "cybersigil"}
def load_cfg():
    try:
        for line in open(CFG):
            k, _, v = line.strip().partition("=")
            if k == "volume": cfg["volume"] = max(0.0, min(1.0, float(v)))
            if k == "enabled": cfg["enabled"] = v.strip().lower() in ("1", "true", "yes")
            if k == "pack": cfg["pack"] = v.strip()
    except FileNotFoundError:
        pass
load_cfg()

NAMES = ["key0", "key1", "key2", "key3", "space", "backspace", "mod", "enter", "hold", "release"]
def load_pack(pack):
    d = os.path.join(PACKS, pack)
    if not os.path.isdir(d):
        print(f"keysound: pack '{pack}' not found, using cybersigil", file=sys.stderr); d = os.path.join(PACKS, "cybersigil")
    out = {}
    for n in NAMES:
        try:
            with wave.open(os.path.join(d, n + ".wav")) as w:
                raw = w.readframes(w.getnframes())
            out[n] = struct.unpack("<%dh" % (len(raw) // 2), raw)
        except FileNotFoundError:
            out[n] = ()
    return out
S = load_pack(cfg["pack"])

# ── mixer: list of (samples, pos); streams to pacat only while something is playing ──
voices, vlock = [], threading.Lock()
proc = None; last_active = 0.0
def player():
    global proc, last_active
    while True:
        with vlock:
            active = bool(voices)
        if not active:
            if proc and time.time() - last_active > 3:
                try: proc.stdin.close(); proc.terminate()
                except Exception: pass
                proc = None
            time.sleep(0.005); continue
        if proc is None:
            proc = subprocess.Popen(["pacat", "--playback", "--raw", "--format=s16le", f"--rate={SR}",
                                     "--channels=1", "--latency-msec=15", "--client-name=keysound",
                                     "--stream-name=typing"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        last_active = time.time()
        buf = [0] * CHUNK
        with vlock:
            keep = []
            for samples, pos in voices:
                end = min(pos + CHUNK, len(samples))
                seg = samples[pos:end]
                for i, v in enumerate(seg): buf[i] += v
                if end < len(samples): keep.append((samples, end))
            voices[:] = keep
        g = cfg["volume"] * 0.8
        out = struct.pack("<%dh" % CHUNK, *[max(-32768, min(32767, int(v * g))) for v in buf])
        try: proc.stdin.write(out); proc.stdin.flush()
        except Exception:
            proc = None
threading.Thread(target=player, daemon=True).start()

def play(name):
    if not cfg["enabled"]: return
    with vlock:
        if S.get(name) and len(voices) < 12: voices.append((S[name], 0))

# ── signals ──
signal.signal(signal.SIGUSR1, lambda *_: cfg.__setitem__("enabled", not cfg["enabled"]))
def reload(*_):
    global S
    load_cfg(); new = load_pack(cfg["pack"])
    with vlock:
        S = new; voices.clear()
signal.signal(signal.SIGHUP, reload)

# ── demo mode: exercise the mixer without keyboard access ──
if "--pack" in sys.argv:
    cfg["pack"] = sys.argv[sys.argv.index("--pack") + 1]; S = load_pack(cfg["pack"])
if "--demo" in sys.argv:
    for n, dt in [("key0",.09),("key1",.07),("key2",.11),("space",.12),("key3",.08),("key0",.06),("backspace",.15),("enter",.5),("hold",.35),("release",.4)]:
        play(n); time.sleep(dt)
    time.sleep(0.8); print("demo done"); sys.exit(0)

# ── keyboards ──
def keyboards():
    nodes = sorted(set(glob.glob("/dev/input/by-path/*-event-kbd") + glob.glob("/dev/input/by-id/*-event-kbd")))
    fds = {}
    for n in nodes:
        try:
            real = os.path.realpath(n)
            if real in fds.values(): continue
            fds[os.open(n, os.O_RDONLY | os.O_NONBLOCK)] = real
        except PermissionError:
            print(f"keysound: no permission for {n} (add yourself to the 'input' group)", file=sys.stderr)
        except OSError:
            pass
    return fds

fds = keyboards()
if not fds:
    print("keysound: no readable keyboard device, exiting", file=sys.stderr); sys.exit(1)
holding = set()
rescan = time.time()
while True:
    r, _, _ = select.select(list(fds), [], [], 2.0)
    if time.time() - rescan > 10:        # pick up hot-plugged keyboards
        for fd in fds: os.close(fd)
        fds = keyboards() or fds; rescan = time.time(); continue
    for fd in r:
        try: data = os.read(fd, EVSZ * 64)
        except OSError: continue
        for off in range(0, len(data) - EVSZ + 1, EVSZ):
            _, _, etype, code, value = struct.unpack_from("llHHi", data, off)
            if etype != EV_KEY or code >= 0x100: continue
            if code in SUPER:
                if value == 1: play("hold")
                elif value == 0: play("release")
                continue
            if value == 1:
                if code in (KEY_ENTER, KEY_KPENTER): play("enter")
                elif code == KEY_SPACE: play("space")
                elif code == KEY_BACKSPACE: play("backspace")
                elif code in MODS: play("mod")
                else: play(random.choice(("key0", "key1", "key2", "key3")))
            elif value == 2:
                if code not in holding:
                    holding.add(code); play("hold")
            elif value == 0 and code in holding:
                holding.discard(code); play("release")
